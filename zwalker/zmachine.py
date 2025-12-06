"""
Z-Machine interpreter for zwalker

A Python implementation of the Z-machine virtual machine,
designed for automated game exploration and testing.
"""

import struct
import copy
import random
from typing import Optional, List, Tuple, Callable, Any
from dataclasses import dataclass, field


@dataclass
class ZHeader:
    """Z-Machine header structure"""
    version: int
    flags1: int
    release: int
    high_memory: int
    initial_pc: int
    dictionary: int
    object_table: int
    globals: int
    static_memory: int
    flags2: int
    serial: str
    abbreviations: int
    file_length: int
    checksum: int
    routines_offset: int = 0
    strings_offset: int = 0


@dataclass
class CallFrame:
    """Call stack frame"""
    return_pc: int
    locals: List[int]
    num_locals: int
    store_var: Optional[int]
    stack_depth: int  # Stack depth at call time


@dataclass
class GameState:
    """Complete game state for save/restore"""
    memory: bytearray
    pc: int
    stack: List[int]
    call_stack: List[CallFrame]
    locals: List[int]
    random_state: Any


class ZMachineError(Exception):
    """Z-Machine runtime error"""
    pass


class ZMachine:
    """Z-Machine interpreter"""

    # Z-String alphabets
    A0 = "abcdefghijklmnopqrstuvwxyz"
    A1 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, data: bytes):
        self.original_data = bytes(data)
        self.memory = bytearray(data)
        self.header = self._parse_header()

        # CPU state
        self.pc = self.header.initial_pc
        self.stack: List[int] = []
        self.call_stack: List[CallFrame] = []
        self.locals: List[int] = [0] * 16

        # I/O
        self.output_buffer = ""
        self.input_callback: Optional[Callable[[str], str]] = None
        self.output_callback: Optional[Callable[[str], None]] = None

        # Interpreter state
        self.running = False
        self.finished = False
        self.waiting_for_input = False
        self.pending_input_callback: Optional[Callable[[str], None]] = None

        # Random number generator
        self.rng = random.Random()

        # Debug
        self.debug = False
        self.instruction_count = 0

        # Player tracking - will be detected on first access
        self._player_object: Optional[int] = None
        self._rooms_container: Optional[int] = None

    def _parse_header(self) -> ZHeader:
        """Parse the 64-byte Z-machine header"""
        version = self.memory[0]

        header = ZHeader(
            version=version,
            flags1=self.memory[1],
            release=struct.unpack('>H', self.memory[2:4])[0],
            high_memory=struct.unpack('>H', self.memory[4:6])[0],
            initial_pc=struct.unpack('>H', self.memory[6:8])[0],
            dictionary=struct.unpack('>H', self.memory[8:10])[0],
            object_table=struct.unpack('>H', self.memory[10:12])[0],
            globals=struct.unpack('>H', self.memory[12:14])[0],
            static_memory=struct.unpack('>H', self.memory[14:16])[0],
            flags2=struct.unpack('>H', self.memory[16:18])[0],
            serial=self.memory[18:24].decode('ascii', errors='ignore'),
            abbreviations=struct.unpack('>H', self.memory[24:26])[0] if version >= 2 else 0,
            file_length=struct.unpack('>H', self.memory[26:28])[0],
            checksum=struct.unpack('>H', self.memory[28:30])[0],
        )

        # Adjust file length based on version
        if version <= 3:
            header.file_length *= 2
        elif version <= 5:
            header.file_length *= 4
        else:
            header.file_length *= 8

        # V6/V7 offsets
        if version in (6, 7):
            header.routines_offset = struct.unpack('>H', self.memory[0x28:0x2A])[0] * 8
            header.strings_offset = struct.unpack('>H', self.memory[0x2A:0x2C])[0] * 8

        return header

    # Memory access
    def read_byte(self, addr: int) -> int:
        return self.memory[addr]

    def read_word(self, addr: int) -> int:
        return (self.memory[addr] << 8) | self.memory[addr + 1]

    def write_byte(self, addr: int, value: int) -> None:
        if addr >= self.header.static_memory:
            raise ZMachineError(f"Write to static memory at 0x{addr:04X}")
        self.memory[addr] = value & 0xFF

    def write_word(self, addr: int, value: int) -> None:
        if addr >= self.header.static_memory:
            raise ZMachineError(f"Write to static memory at 0x{addr:04X}")
        self.memory[addr] = (value >> 8) & 0xFF
        self.memory[addr + 1] = value & 0xFF

    # Stack operations
    def push(self, value: int) -> None:
        self.stack.append(value & 0xFFFF)

    def pop(self) -> int:
        if not self.stack:
            raise ZMachineError("Stack underflow")
        return self.stack.pop()

    # Variable access (0=stack, 1-15=locals, 16-255=globals)
    def get_variable(self, var_num: int) -> int:
        if var_num == 0:
            return self.pop()
        elif var_num < 16:
            return self.locals[var_num - 1]
        else:
            addr = self.header.globals + (var_num - 16) * 2
            return self.read_word(addr)

    def set_variable(self, var_num: int, value: int) -> None:
        value = value & 0xFFFF
        if var_num == 0:
            self.push(value)
        elif var_num < 16:
            self.locals[var_num - 1] = value
        else:
            addr = self.header.globals + (var_num - 16) * 2
            self.write_word(addr, value)

    def get_operand(self, operand: Any) -> int:
        """Evaluate an operand (constant or variable reference)"""
        if isinstance(operand, tuple) and operand[0] == 'var':
            return self.get_variable(operand[1])
        return operand

    # Address unpacking
    def unpack_address(self, packed: int, is_string: bool = False) -> int:
        v = self.header.version
        if v <= 3:
            return packed * 2
        elif v <= 5:
            return packed * 4
        elif v in (6, 7):
            offset = self.header.strings_offset if is_string else self.header.routines_offset
            return packed * 4 + offset
        else:  # V8
            return packed * 8

    # Z-String decoding
    def decode_zstring(self, addr: int) -> Tuple[str, int]:
        """Decode Z-string at address, return (string, next_address)"""
        result = []
        alphabet = 0
        lock_alphabet = 0
        abbrev_table = 0
        zscii_state = 0
        zscii_high = 0

        # Version-specific A2
        if self.header.version == 1:
            A2 = " 0123456789.,!?_#'\"/\\<-:()"
        else:
            A2 = " \n0123456789.,!?_#'\"/\\-:()"

        while True:
            word = self.read_word(addr)
            addr += 2

            chars = [
                (word >> 10) & 0x1F,
                (word >> 5) & 0x1F,
                word & 0x1F
            ]

            for c in chars:
                # 10-bit ZSCII escape
                if zscii_state == 1:
                    zscii_high = c
                    zscii_state = 2
                    continue
                elif zscii_state == 2:
                    zscii_code = (zscii_high << 5) | c
                    if zscii_code > 0:
                        result.append(chr(zscii_code))
                    zscii_state = 0
                    alphabet = lock_alphabet
                    continue

                # Abbreviation mode
                if abbrev_table > 0:
                    if self.header.version >= 2 and self.header.abbreviations:
                        abbr_addr = self.header.abbreviations + 2 * (32 * (abbrev_table - 1) + c)
                        word_addr = self.read_word(abbr_addr)
                        abbr_str, _ = self.decode_zstring(word_addr * 2)
                        result.append(abbr_str)
                    abbrev_table = 0
                    alphabet = lock_alphabet
                    continue

                # Z-char 0: space
                if c == 0:
                    result.append(' ')
                    alphabet = lock_alphabet
                    continue

                # Z-char 1
                if c == 1:
                    if self.header.version == 1:
                        result.append('\n')
                    else:
                        abbrev_table = 1
                    continue

                # Z-char 2
                if c == 2:
                    if self.header.version == 1:
                        alphabet = (alphabet + 1) % 3
                    elif self.header.version == 2:
                        alphabet = (lock_alphabet + 1) % 3
                    else:
                        abbrev_table = 2
                    continue

                # Z-char 3
                if c == 3:
                    if self.header.version == 1:
                        alphabet = (alphabet + 2) % 3
                    elif self.header.version == 2:
                        alphabet = (lock_alphabet + 2) % 3
                    else:
                        abbrev_table = 3
                    continue

                # Z-char 4
                if c == 4:
                    if self.header.version <= 2:
                        lock_alphabet = (lock_alphabet + 1) % 3
                        alphabet = lock_alphabet
                    else:
                        alphabet = 1
                    continue

                # Z-char 5
                if c == 5:
                    if self.header.version <= 2:
                        lock_alphabet = (lock_alphabet + 2) % 3
                        alphabet = lock_alphabet
                    else:
                        alphabet = 2
                    continue

                # Z-char 6 in A2 = ZSCII escape
                if c == 6 and alphabet == 2:
                    zscii_state = 1
                    continue

                # Regular character (6-31)
                if 6 <= c <= 31:
                    idx = c - 6
                    if alphabet == 0 and idx < len(self.A0):
                        result.append(self.A0[idx])
                    elif alphabet == 1 and idx < len(self.A1):
                        result.append(self.A1[idx])
                    elif alphabet == 2 and idx < len(A2):
                        result.append(A2[idx])

                # Reset alphabet
                if self.header.version >= 3:
                    alphabet = 0
                else:
                    alphabet = lock_alphabet

            # End bit
            if word & 0x8000:
                break

        return ''.join(result), addr

    # Object system
    def _get_object_address(self, obj_num: int) -> Optional[int]:
        if obj_num == 0:
            return None

        if self.header.version <= 3:
            tree_base = self.header.object_table + 62  # 31 property defaults
            obj_size = 9
            max_obj = 255
        else:
            tree_base = self.header.object_table + 126  # 63 property defaults
            obj_size = 14
            max_obj = 65535

        if obj_num > max_obj:
            return None

        addr = tree_base + (obj_num - 1) * obj_size
        # Bounds check - ensure object fits in memory
        if addr < 0 or addr + obj_size > len(self.memory):
            return None

        return addr

    def get_object_parent(self, obj_num: int) -> int:
        addr = self._get_object_address(obj_num)
        if not addr:
            return 0
        if self.header.version <= 3:
            return self.read_byte(addr + 4)
        else:
            return self.read_word(addr + 6)

    def get_object_sibling(self, obj_num: int) -> int:
        addr = self._get_object_address(obj_num)
        if not addr:
            return 0
        if self.header.version <= 3:
            return self.read_byte(addr + 5)
        else:
            return self.read_word(addr + 8)

    def get_object_child(self, obj_num: int) -> int:
        addr = self._get_object_address(obj_num)
        if not addr:
            return 0
        if self.header.version <= 3:
            return self.read_byte(addr + 6)
        else:
            return self.read_word(addr + 10)

    def set_object_parent(self, obj_num: int, parent: int) -> None:
        addr = self._get_object_address(obj_num)
        if not addr:
            return
        if self.header.version <= 3:
            self.write_byte(addr + 4, parent)
        else:
            self.write_word(addr + 6, parent)

    def set_object_sibling(self, obj_num: int, sibling: int) -> None:
        addr = self._get_object_address(obj_num)
        if not addr:
            return
        if self.header.version <= 3:
            self.write_byte(addr + 5, sibling)
        else:
            self.write_word(addr + 8, sibling)

    def set_object_child(self, obj_num: int, child: int) -> None:
        addr = self._get_object_address(obj_num)
        if not addr:
            return
        if self.header.version <= 3:
            self.write_byte(addr + 6, child)
        else:
            self.write_word(addr + 10, child)

    def get_object_prop_addr(self, obj_num: int) -> int:
        addr = self._get_object_address(obj_num)
        if not addr:
            return 0
        if self.header.version <= 3:
            return self.read_word(addr + 7)
        else:
            return self.read_word(addr + 12)

    def get_object_name(self, obj_num: int) -> str:
        prop_addr = self.get_object_prop_addr(obj_num)
        if not prop_addr:
            return ""
        text_len = self.read_byte(prop_addr)
        if text_len == 0:
            return ""
        name, _ = self.decode_zstring(prop_addr + 1)
        return name

    def get_attribute(self, obj_num: int, attr: int) -> bool:
        addr = self._get_object_address(obj_num)
        if not addr:
            return False
        byte_idx = attr // 8
        bit_idx = 7 - (attr % 8)
        return bool(self.read_byte(addr + byte_idx) & (1 << bit_idx))

    def set_attribute(self, obj_num: int, attr: int) -> None:
        addr = self._get_object_address(obj_num)
        if not addr:
            return
        byte_idx = attr // 8
        bit_idx = 7 - (attr % 8)
        val = self.read_byte(addr + byte_idx)
        self.write_byte(addr + byte_idx, val | (1 << bit_idx))

    def clear_attribute(self, obj_num: int, attr: int) -> None:
        addr = self._get_object_address(obj_num)
        if not addr:
            return
        byte_idx = attr // 8
        bit_idx = 7 - (attr % 8)
        val = self.read_byte(addr + byte_idx)
        self.write_byte(addr + byte_idx, val & ~(1 << bit_idx))

    def insert_object(self, obj: int, dest: int) -> None:
        """Move object to be first child of dest"""
        self.remove_object(obj)
        if dest == 0:
            return
        old_child = self.get_object_child(dest)
        self.set_object_parent(obj, dest)
        self.set_object_sibling(obj, old_child)
        self.set_object_child(dest, obj)

    def remove_object(self, obj: int) -> None:
        """Remove object from its parent"""
        parent = self.get_object_parent(obj)
        if parent == 0:
            return

        if self.get_object_child(parent) == obj:
            self.set_object_child(parent, self.get_object_sibling(obj))
        else:
            prev = self.get_object_child(parent)
            while prev and self.get_object_sibling(prev) != obj:
                prev = self.get_object_sibling(prev)
            if prev:
                self.set_object_sibling(prev, self.get_object_sibling(obj))

        self.set_object_parent(obj, 0)
        self.set_object_sibling(obj, 0)

    # Property access
    def _find_property(self, obj_num: int, prop_num: int) -> Tuple[int, int]:
        """Find property, return (data_addr, size) or (0, 0) if not found"""
        prop_addr = self.get_object_prop_addr(obj_num)
        if not prop_addr:
            return 0, 0

        # Skip object name
        text_len = self.read_byte(prop_addr)
        prop_addr += 1 + text_len * 2

        while True:
            size_byte = self.read_byte(prop_addr)
            if size_byte == 0:
                break

            if self.header.version <= 3:
                pnum = size_byte & 0x1F
                psize = (size_byte >> 5) + 1
                prop_addr += 1
            else:
                pnum = size_byte & 0x3F
                if size_byte & 0x80:
                    size_byte2 = self.read_byte(prop_addr + 1)
                    psize = size_byte2 & 0x3F
                    if psize == 0:
                        psize = 64
                    prop_addr += 2
                else:
                    psize = 1 if (size_byte & 0x40) == 0 else 2
                    prop_addr += 1

            if pnum == prop_num:
                return prop_addr, psize

            prop_addr += psize

        return 0, 0

    def get_property(self, obj_num: int, prop_num: int) -> int:
        data_addr, size = self._find_property(obj_num, prop_num)
        if data_addr == 0:
            # Return default
            default_addr = self.header.object_table + (prop_num - 1) * 2
            return self.read_word(default_addr)
        if size == 1:
            return self.read_byte(data_addr)
        else:
            return self.read_word(data_addr)

    def put_property(self, obj_num: int, prop_num: int, value: int) -> None:
        data_addr, size = self._find_property(obj_num, prop_num)
        if data_addr == 0:
            raise ZMachineError(f"Property {prop_num} not found on object {obj_num}")
        if size == 1:
            self.write_byte(data_addr, value)
        else:
            self.write_word(data_addr, value)

    def get_property_addr(self, obj_num: int, prop_num: int) -> int:
        data_addr, _ = self._find_property(obj_num, prop_num)
        return data_addr

    def get_property_len(self, data_addr: int) -> int:
        if data_addr == 0:
            return 0
        size_byte = self.read_byte(data_addr - 1)
        if self.header.version <= 3:
            return (size_byte >> 5) + 1
        else:
            if size_byte & 0x80:
                psize = size_byte & 0x3F
                return 64 if psize == 0 else psize
            else:
                return 2 if (size_byte & 0x40) else 1

    def get_next_property(self, obj_num: int, prop_num: int) -> int:
        prop_addr = self.get_object_prop_addr(obj_num)
        if not prop_addr:
            return 0

        # Skip name
        text_len = self.read_byte(prop_addr)
        prop_addr += 1 + text_len * 2

        if prop_num == 0:
            # Return first property
            size_byte = self.read_byte(prop_addr)
            if size_byte == 0:
                return 0
            if self.header.version <= 3:
                return size_byte & 0x1F
            else:
                return size_byte & 0x3F

        # Find prop_num, then return next
        while True:
            size_byte = self.read_byte(prop_addr)
            if size_byte == 0:
                return 0

            if self.header.version <= 3:
                pnum = size_byte & 0x1F
                psize = (size_byte >> 5) + 1
                prop_addr += 1
            else:
                pnum = size_byte & 0x3F
                if size_byte & 0x80:
                    size_byte2 = self.read_byte(prop_addr + 1)
                    psize = size_byte2 & 0x3F
                    if psize == 0:
                        psize = 64
                    prop_addr += 2
                else:
                    psize = 1 if (size_byte & 0x40) == 0 else 2
                    prop_addr += 1

            if pnum == prop_num:
                prop_addr += psize
                size_byte = self.read_byte(prop_addr)
                if size_byte == 0:
                    return 0
                if self.header.version <= 3:
                    return size_byte & 0x1F
                else:
                    return size_byte & 0x3F

            prop_addr += psize

        return 0

    # Player and room detection
    def _detect_rooms_container(self) -> Optional[int]:
        """
        Detect the ROOMS container object.

        In Infocom games, all room objects share a common parent (typically
        an object named "ROOMS" or similar). We find this by looking for
        the object that has the most children with multiple properties
        (rooms typically have direction properties).
        """
        if self._rooms_container is not None:
            return self._rooms_container

        from collections import Counter
        parent_counts = Counter()

        max_obj = 255 if self.header.version <= 3 else 2000

        for obj_num in range(1, min(max_obj, 256)):
            parent = self.get_object_parent(obj_num)
            if parent > 0:
                # Count objects with multiple properties (likely rooms)
                prop_count = self._count_properties(obj_num)
                if prop_count >= 3:
                    parent_counts[parent] += 1

        if parent_counts:
            self._rooms_container = parent_counts.most_common(1)[0][0]

        return self._rooms_container

    def _count_properties(self, obj_num: int) -> int:
        """Count number of properties on an object"""
        try:
            prop_addr = self.get_object_prop_addr(obj_num)
            if not prop_addr or prop_addr >= len(self.memory):
                return 0

            # Skip object name
            text_len = self.read_byte(prop_addr)
            prop_addr += 1 + text_len * 2

            if prop_addr >= len(self.memory):
                return 0

            count = 0
            while prop_addr < len(self.memory) - 1:
                size_byte = self.read_byte(prop_addr)
                if size_byte == 0:
                    break
                count += 1

                if self.header.version <= 3:
                    psize = (size_byte >> 5) + 1
                else:
                    if size_byte & 0x80:
                        if prop_addr + 1 >= len(self.memory):
                            break
                        size_byte2 = self.read_byte(prop_addr + 1)
                        psize = size_byte2 & 0x3F
                        if psize == 0:
                            psize = 64
                        prop_addr += 1
                    else:
                        psize = 1 if (size_byte & 0x40) == 0 else 2

                prop_addr += 1 + psize

            return count
        except (IndexError, struct.error):
            return 0

    def _is_room(self, obj_num: int) -> bool:
        """Check if an object is a room (child of ROOMS container)"""
        rooms_container = self._detect_rooms_container()
        if rooms_container is None:
            return False
        return self.get_object_parent(obj_num) == rooms_container

    def detect_player_object(self) -> Optional[int]:
        """
        Detect the player object.

        The player object is typically:
        1. An object whose parent is a room
        2. One of the first few objects (low object number)
        3. Often object 4-10 in Infocom games

        We look for an object in the low range whose parent is a room.
        """
        if self._player_object is not None:
            return self._player_object

        rooms_container = self._detect_rooms_container()
        if rooms_container is None:
            return None

        # Check objects 1-30 for potential player objects
        for obj_num in range(1, 31):
            parent = self.get_object_parent(obj_num)
            # Is this object inside a room?
            if parent > 0 and self._is_room(parent):
                # It's in a room - likely the player or an object
                # The player is usually one of the very first such objects
                name = self.get_object_name(obj_num)
                # Some common player object names
                if name and any(n in name.lower() for n in
                              ['player', 'adventurer', 'you', 'cretin', 'protagonist']):
                    self._player_object = obj_num
                    return obj_num

        # Fallback: just find the first object whose parent is a room
        for obj_num in range(1, 31):
            parent = self.get_object_parent(obj_num)
            if parent > 0 and self._is_room(parent):
                self._player_object = obj_num
                return obj_num

        return None

    def get_current_room(self) -> Optional[int]:
        """
        Get the current room object number.

        Different games use different conventions:
        - Infocom games: Global 0 holds the room object number
        - Inform games: Player object's parent is the room

        We try both methods and return a valid-looking room.
        """
        # Method 1: Infocom convention - global 0 is the room
        room = self.read_word(self.header.globals)
        if room > 0 and room < 1000:  # Reasonable object number
            # Verify it looks like a valid object
            try:
                name = self.get_object_name(room)
                if name and len(name) > 0:
                    return room
            except:
                pass

        # Method 2: Inform convention - find player and get parent
        player = self.detect_player_object()
        if player:
            parent = self.get_object_parent(player)
            if parent > 0 and parent < 1000:
                try:
                    name = self.get_object_name(parent)
                    if name and len(name) > 0:
                        return parent
                except:
                    pass

        # Fallback to global 0 even if large (some games use high object numbers)
        if room > 0:
            try:
                name = self.get_object_name(room)
                if name and len(name) > 0:
                    return room
            except:
                pass

        return None

    def get_current_room_name(self) -> str:
        """Get the name of the current room"""
        room = self.get_current_room()
        if room:
            return self.get_object_name(room)
        return ""

    def get_all_rooms(self) -> List[Tuple[int, str]]:
        """
        Get all room objects in the game.

        Returns a list of (object_number, name) tuples for all rooms.
        This uses static analysis - no game execution required.
        """
        rooms = []
        rooms_container = self._detect_rooms_container()
        if rooms_container is None:
            return rooms

        max_obj = 255 if self.header.version <= 3 else 2000

        for obj_num in range(1, min(max_obj, 256)):
            if self.get_object_parent(obj_num) == rooms_container:
                name = self.get_object_name(obj_num)
                if name:
                    rooms.append((obj_num, name))

        return rooms

    # Object detection for game objects (not rooms)
    # In Infocom games, attribute 17 typically marks takeable objects
    ATTR_TAKEABLE = 17

    def is_takeable(self, obj_num: int) -> bool:
        """Check if an object can be picked up (has takeable attribute)"""
        return self.get_attribute(obj_num, self.ATTR_TAKEABLE)

    def get_objects_in_room(self, room_num: Optional[int] = None) -> List[Tuple[int, str]]:
        """
        Get all objects in a room.

        Returns (object_number, name) tuples for objects whose parent is the room.
        If room_num is None, uses current room.
        """
        if room_num is None:
            room_num = self.get_current_room()
        if room_num is None:
            return []

        objects = []
        max_obj = 255 if self.header.version <= 3 else 2000
        rooms = set(obj for obj, _ in self.get_all_rooms())

        for obj_num in range(1, min(max_obj, 256)):
            try:
                if obj_num in rooms:
                    continue
                if self.get_object_parent(obj_num) == room_num:
                    name = self.get_object_name(obj_num)
                    if name:
                        objects.append((obj_num, name))
            except (IndexError, struct.error):
                continue

        return objects

    def get_takeable_objects_in_room(self, room_num: Optional[int] = None) -> List[Tuple[int, str]]:
        """Get takeable objects in a room"""
        objects = self.get_objects_in_room(room_num)
        return [(obj, name) for obj, name in objects if self.is_takeable(obj)]

    def get_inventory(self) -> List[Tuple[int, str]]:
        """
        Get objects carried by the player.

        Returns (object_number, name) tuples.
        """
        player = self.detect_player_object()
        if player is None:
            return []

        inventory = []
        max_obj = 255 if self.header.version <= 3 else 2000

        for obj_num in range(1, min(max_obj, 256)):
            if self.get_object_parent(obj_num) == player:
                name = self.get_object_name(obj_num)
                if name:
                    inventory.append((obj_num, name))

        return inventory

    # Dictionary
    def get_dictionary_words(self) -> List[str]:
        """Get all words from dictionary"""
        words = []
        addr = self.header.dictionary

        num_seps = self.read_byte(addr)
        addr += 1 + num_seps

        entry_len = self.read_byte(addr)
        addr += 1
        num_entries = struct.unpack('>h', bytes(self.memory[addr:addr+2]))[0]
        addr += 2

        for _ in range(abs(num_entries)):
            word, _ = self.decode_zstring(addr)
            words.append(word.strip())
            addr += entry_len

        return words

    def get_dictionary_words_by_type(self) -> dict:
        """
        Get dictionary words categorized by type.

        Returns dict with keys: 'verbs', 'nouns', 'adjectives', 'directions', 'prepositions'

        Word types are encoded in the extra bytes after the encoded word text.
        This encoding is Infocom-specific and may not work for all games.
        Falls back to heuristic categorization if type bytes don't look valid.

        Common Infocom type bytes:
        - 0x41 (65): Verbs
        - 0x80 (128): Nouns (objects)
        - 0x22 (34): Adjectives
        - 0x13 (19): Compass directions
        - 0x18 (24): Vertical directions (up/down/in/out)
        - 0x08 (8): Prepositions
        """
        result = {
            'verbs': [],
            'nouns': [],
            'adjectives': [],
            'directions': [],
            'prepositions': [],
            'other': []
        }

        addr = self.header.dictionary
        num_seps = self.read_byte(addr)
        addr += 1 + num_seps

        entry_len = self.read_byte(addr)
        addr += 1
        num_entries = struct.unpack('>h', bytes(self.memory[addr:addr+2]))[0]
        addr += 2

        # Encoded word is 4 bytes in V1-3, 6 bytes in V4+
        word_bytes = 4 if self.header.version <= 3 else 6

        # First pass: try to use Infocom-style type bytes
        words_with_types = []
        has_valid_types = False

        for i in range(abs(num_entries)):
            word_addr = addr + i * entry_len
            word, _ = self.decode_zstring(word_addr)
            word = word.strip()

            word_type = 0
            if entry_len > word_bytes:
                word_type = self.read_byte(word_addr + word_bytes)
                # Check if this looks like a valid Infocom type
                if word_type in (0x41, 0x80, 0x22, 0x13, 0x18, 0x33, 0x08, 4, 8, 19, 24, 34, 51, 65, 128):
                    has_valid_types = True

            words_with_types.append((word, word_type))

        # If we found valid type bytes, use them
        if has_valid_types:
            for word, word_type in words_with_types:
                if word_type == 0x41 or word_type == 65:  # Verb
                    result['verbs'].append(word)
                elif word_type == 0x80 or word_type == 128:  # Noun
                    result['nouns'].append(word)
                elif word_type == 0x22 or word_type == 34:  # Adjective
                    result['adjectives'].append(word)
                elif word_type in (0x13, 0x18, 0x33, 19, 24, 51):  # Directions
                    result['directions'].append(word)
                elif word_type == 0x08 or word_type == 8:  # Preposition
                    result['prepositions'].append(word)
                else:
                    result['other'].append(word)
        else:
            # Fallback: use heuristic categorization based on word content
            result = self._categorize_words_heuristically([w for w, _ in words_with_types])

        return result

    def _categorize_words_heuristically(self, words: list) -> dict:
        """
        Categorize words using heuristics when type bytes aren't available.

        This is a fallback for non-Infocom games.
        """
        # Known word lists
        known_directions = {
            'n', 's', 'e', 'w', 'north', 'south', 'east', 'west',
            'ne', 'nw', 'se', 'sw', 'northeast', 'northwest', 'southeast', 'southwest',
            'up', 'down', 'u', 'd', 'in', 'out', 'enter', 'exit',
            'northe', 'northw', 'southe', 'southw'  # truncated versions
        }

        known_verbs = {
            'take', 'get', 'drop', 'put', 'give', 'throw', 'open', 'close', 'shut',
            'read', 'examine', 'look', 'x', 'l', 'push', 'pull', 'turn', 'move',
            'lift', 'light', 'unlock', 'lock', 'eat', 'drink', 'wear', 'remove',
            'attack', 'kill', 'hit', 'tie', 'untie', 'pour', 'fill', 'empty',
            'climb', 'break', 'cut', 'dig', 'wait', 'z', 'jump', 'sleep',
            'wake', 'save', 'restore', 'quit', 'inventory', 'i', 'score',
            'ask', 'tell', 'say', 'shout', 'yell', 'whisper', 'sing',
            'swim', 'wave', 'point', 'rub', 'touch', 'feel', 'smell', 'listen',
            'taste', 'search', 'find', 'follow', 'buy', 'sell', 'count'
        }

        known_prepositions = {
            'to', 'at', 'in', 'on', 'with', 'from', 'into', 'onto', 'under',
            'behind', 'through', 'about', 'for', 'around', 'across', 'over',
            'off', 'out', 'up', 'down', 'away', 'toward', 'towards'
        }

        known_articles = {'a', 'an', 'the', 'some', 'any', 'all', 'my', 'your'}

        result = {
            'verbs': [],
            'nouns': [],
            'adjectives': [],
            'directions': [],
            'prepositions': [],
            'other': []
        }

        for word in words:
            word_lower = word.lower()

            if word_lower in known_directions:
                result['directions'].append(word)
            elif word_lower in known_verbs or word_lower[:6] in known_verbs:
                result['verbs'].append(word)
            elif word_lower in known_prepositions:
                result['prepositions'].append(word)
            elif word_lower in known_articles:
                result['other'].append(word)
            else:
                # Assume most other words are nouns or adjectives
                # This is imperfect but works for basic exploration
                result['nouns'].append(word)

        return result

    # State management
    def save_state(self) -> GameState:
        """Save complete game state"""
        return GameState(
            memory=bytearray(self.memory[:self.header.static_memory]),
            pc=self.pc,
            stack=list(self.stack),
            call_stack=[copy.copy(f) for f in self.call_stack],
            locals=list(self.locals),
            random_state=self.rng.getstate()
        )

    def restore_state(self, state: GameState) -> None:
        """Restore game state"""
        self.memory[:self.header.static_memory] = state.memory
        self.pc = state.pc
        self.stack = list(state.stack)
        self.call_stack = [copy.copy(f) for f in state.call_stack]
        self.locals = list(state.locals)
        self.rng.setstate(state.random_state)
        self.waiting_for_input = False
        self.pending_input_callback = None

    def restart(self) -> None:
        """Restart game"""
        self.memory = bytearray(self.original_data)
        self.header = self._parse_header()
        self.pc = self.header.initial_pc
        self.stack = []
        self.call_stack = []
        self.locals = [0] * 16
        self.output_buffer = ""
        self.running = False
        self.finished = False
        self.waiting_for_input = False

    # Output
    def print_text(self, text: str) -> None:
        self.output_buffer += text
        if self.output_callback:
            self.output_callback(text)

    def print_num(self, num: int) -> None:
        # Convert to signed
        if num > 32767:
            num -= 65536
        self.print_text(str(num))

    def print_char(self, char: int) -> None:
        self.print_text(chr(char))

    def print_object(self, obj_num: int) -> None:
        self.print_text(self.get_object_name(obj_num))

    def print_addr(self, addr: int) -> None:
        text, _ = self.decode_zstring(addr)
        self.print_text(text)

    def print_paddr(self, packed: int) -> None:
        addr = self.unpack_address(packed, is_string=True)
        text, _ = self.decode_zstring(addr)
        self.print_text(text)

    # Instruction execution
    def decode_instruction(self) -> Tuple[str, List[Any], Optional[int], Optional[Tuple[int, bool]], Optional[str]]:
        """
        Decode instruction at PC.
        Returns (opcode_name, operands, store_var, branch_info, inline_text)
        branch_info is (offset, branch_on_true) or None
        """
        start_pc = self.pc
        opcode_byte = self.read_byte(self.pc)
        self.pc += 1

        # Determine form
        if opcode_byte == 0xBE and self.header.version >= 5:
            return self._decode_extended()
        elif opcode_byte & 0xC0 == 0xC0:
            if opcode_byte < 0xE0:
                return self._decode_var_2op(opcode_byte & 0x1F)
            else:
                return self._decode_var_var(opcode_byte & 0x1F)
        elif opcode_byte & 0x80 == 0x80:
            return self._decode_short(opcode_byte)
        else:
            return self._decode_long(opcode_byte)

    def _read_operands_from_types(self, types_byte: int, count: int = 4) -> List[Any]:
        """Read operands based on types byte"""
        operands = []
        for i in range(count):
            op_type = (types_byte >> (6 - i * 2)) & 0x03
            if op_type == 0x03:  # Omitted
                break
            elif op_type == 0x00:  # Large constant
                operands.append(self.read_word(self.pc))
                self.pc += 2
            elif op_type == 0x01:  # Small constant
                operands.append(self.read_byte(self.pc))
                self.pc += 1
            elif op_type == 0x02:  # Variable
                operands.append(('var', self.read_byte(self.pc)))
                self.pc += 1
        return operands

    def _read_branch(self) -> Tuple[int, bool]:
        """Read branch info, return (offset, branch_on_true)"""
        branch_byte = self.read_byte(self.pc)
        self.pc += 1
        branch_on_true = bool(branch_byte & 0x80)

        if branch_byte & 0x40:
            offset = branch_byte & 0x3F
        else:
            offset = ((branch_byte & 0x3F) << 8) | self.read_byte(self.pc)
            self.pc += 1
            if offset & 0x2000:
                offset = offset - 0x4000

        return offset, branch_on_true

    # Opcode tables
    SHORT_0OP = {
        0x00: ("rtrue", False, False),
        0x01: ("rfalse", False, False),
        0x02: ("print", False, False),
        0x03: ("print_ret", False, False),
        0x04: ("nop", False, False),
        0x05: ("save", False, True),  # V1-3 branch, V4+ store
        0x06: ("restore", False, True),  # V1-3 branch, V4+ store
        0x07: ("restart", False, False),
        0x08: ("ret_popped", False, False),
        0x09: ("pop", False, False),
        0x0A: ("quit", False, False),
        0x0B: ("new_line", False, False),
        0x0C: ("show_status", False, False),
        0x0D: ("verify", False, True),
        0x0E: ("extended", False, False),
        0x0F: ("piracy", False, True),
    }

    SHORT_1OP = {
        0x00: ("jz", False, True),
        0x01: ("get_sibling", True, True),
        0x02: ("get_child", True, True),
        0x03: ("get_parent", True, False),
        0x04: ("get_prop_len", True, False),
        0x05: ("inc", False, False),
        0x06: ("dec", False, False),
        0x07: ("print_addr", False, False),
        0x08: ("call_1s", True, False),
        0x09: ("remove_obj", False, False),
        0x0A: ("print_obj", False, False),
        0x0B: ("ret", False, False),
        0x0C: ("jump", False, False),
        0x0D: ("print_paddr", False, False),
        0x0E: ("load", True, False),
        0x0F: ("not", True, False),  # V1-4: not, V5+: call_1n
    }

    LONG_2OP = {
        0x01: ("je", False, True),
        0x02: ("jl", False, True),
        0x03: ("jg", False, True),
        0x04: ("dec_chk", False, True),
        0x05: ("inc_chk", False, True),
        0x06: ("jin", False, True),
        0x07: ("test", False, True),
        0x08: ("or", True, False),
        0x09: ("and", True, False),
        0x0A: ("test_attr", False, True),
        0x0B: ("set_attr", False, False),
        0x0C: ("clear_attr", False, False),
        0x0D: ("store", False, False),
        0x0E: ("insert_obj", False, False),
        0x0F: ("loadw", True, False),
        0x10: ("loadb", True, False),
        0x11: ("get_prop", True, False),
        0x12: ("get_prop_addr", True, False),
        0x13: ("get_next_prop", True, False),
        0x14: ("add", True, False),
        0x15: ("sub", True, False),
        0x16: ("mul", True, False),
        0x17: ("div", True, False),
        0x18: ("mod", True, False),
        0x19: ("call_2s", True, False),
        0x1A: ("call_2n", False, False),
        0x1B: ("set_colour", False, False),
        0x1C: ("throw", False, False),
    }

    VAR_VAR = {
        0x00: ("call", True, False),
        0x01: ("storew", False, False),
        0x02: ("storeb", False, False),
        0x03: ("put_prop", False, False),
        0x04: ("sread", False, False),
        0x05: ("print_char", False, False),
        0x06: ("print_num", False, False),
        0x07: ("random", True, False),
        0x08: ("push", False, False),
        0x09: ("pull", False, False),
        0x0A: ("split_window", False, False),
        0x0B: ("set_window", False, False),
        0x0C: ("call_vs2", True, False),
        0x0D: ("erase_window", False, False),
        0x0E: ("erase_line", False, False),
        0x0F: ("set_cursor", False, False),
        0x10: ("get_cursor", False, False),
        0x11: ("set_text_style", False, False),
        0x12: ("buffer_mode", False, False),
        0x13: ("output_stream", False, False),
        0x14: ("input_stream", False, False),
        0x15: ("sound_effect", False, False),
        0x16: ("read_char", True, False),
        0x17: ("scan_table", True, True),
        0x18: ("not", True, False),
        0x19: ("call_vn", False, False),
        0x1A: ("call_vn2", False, False),
        0x1B: ("tokenise", False, False),
        0x1C: ("encode_text", False, False),
        0x1D: ("copy_table", False, False),
        0x1E: ("print_table", False, False),
        0x1F: ("check_arg_count", False, True),
    }

    EXTENDED = {
        0x00: ("save", True, False),
        0x01: ("restore", True, False),
        0x02: ("log_shift", True, False),
        0x03: ("art_shift", True, False),
        0x04: ("set_font", True, False),
        0x09: ("save_undo", True, False),
        0x0A: ("restore_undo", True, False),
        0x0B: ("print_unicode", False, False),
        0x0C: ("check_unicode", True, False),
    }

    def _decode_short(self, opcode: int):
        op_type = (opcode >> 4) & 0x03
        opnum = opcode & 0x0F

        operands = []
        if op_type != 0x03:
            if op_type == 0x00:  # Large constant
                operands.append(self.read_word(self.pc))
                self.pc += 2
            elif op_type == 0x01:  # Small constant
                operands.append(self.read_byte(self.pc))
                self.pc += 1
            elif op_type == 0x02:  # Variable
                operands.append(('var', self.read_byte(self.pc)))
                self.pc += 1

        if op_type == 0x03:
            info = self.SHORT_0OP.get(opnum, (f"0op_{opnum:02x}", False, False))
        else:
            info = self.SHORT_1OP.get(opnum, (f"1op_{opnum:02x}", False, False))

        name, has_store, has_branch = info

        # Handle print/print_ret inline text
        text = None
        if name in ("print", "print_ret"):
            text, self.pc = self.decode_zstring(self.pc)

        # V4+ save/restore have store instead of branch
        if op_type == 0x03 and opnum in (0x05, 0x06) and self.header.version >= 4:
            has_store = True
            has_branch = False

        # V5+: 1OP:0F changes from 'not' (has store) to 'call_1n' (no store)
        if op_type != 0x03 and opnum == 0x0F and self.header.version >= 5:
            name = "call_1n"
            has_store = False

        # V5+: 0OP:09 changes from 'pop' (no store) to 'catch' (has store)
        if op_type == 0x03 and opnum == 0x09 and self.header.version >= 5:
            name = "catch"
            has_store = True

        store_var = None
        if has_store:
            store_var = self.read_byte(self.pc)
            self.pc += 1

        branch = None
        if has_branch:
            branch = self._read_branch()

        return name, operands, store_var, branch, text

    def _decode_long(self, opcode: int):
        opnum = opcode & 0x1F

        operands = []
        if opcode & 0x40:
            operands.append(('var', self.read_byte(self.pc)))
        else:
            operands.append(self.read_byte(self.pc))
        self.pc += 1

        if opcode & 0x20:
            operands.append(('var', self.read_byte(self.pc)))
        else:
            operands.append(self.read_byte(self.pc))
        self.pc += 1

        info = self.LONG_2OP.get(opnum, (f"2op_{opnum:02x}", False, False))
        name, has_store, has_branch = info

        store_var = None
        if has_store:
            store_var = self.read_byte(self.pc)
            self.pc += 1

        branch = None
        if has_branch:
            branch = self._read_branch()

        return name, operands, store_var, branch, None

    def _decode_var_2op(self, opnum: int):
        types_byte = self.read_byte(self.pc)
        self.pc += 1
        operands = self._read_operands_from_types(types_byte)

        info = self.LONG_2OP.get(opnum, (f"2op_{opnum:02x}", False, False))
        name, has_store, has_branch = info

        store_var = None
        if has_store:
            store_var = self.read_byte(self.pc)
            self.pc += 1

        branch = None
        if has_branch:
            branch = self._read_branch()

        return name, operands, store_var, branch, None

    def _decode_var_var(self, opnum: int):
        types_byte = self.read_byte(self.pc)
        self.pc += 1
        operands = self._read_operands_from_types(types_byte)

        # Extended operands for call_vs2/call_vn2
        if opnum in (0x0C, 0x1A) and len(operands) == 4:
            types_byte2 = self.read_byte(self.pc)
            self.pc += 1
            operands.extend(self._read_operands_from_types(types_byte2))

        info = self.VAR_VAR.get(opnum, (f"var_{opnum:02x}", False, False))
        name, has_store, has_branch = info

        # V5+: VAR:04 changes from 'sread' (no store) to 'aread' (has store)
        if opnum == 0x04 and self.header.version >= 5:
            name = "aread"
            has_store = True

        store_var = None
        if has_store:
            store_var = self.read_byte(self.pc)
            self.pc += 1

        branch = None
        if has_branch:
            branch = self._read_branch()

        return name, operands, store_var, branch, None

    def _decode_extended(self):
        ext_opnum = self.read_byte(self.pc)
        self.pc += 1
        types_byte = self.read_byte(self.pc)
        self.pc += 1
        operands = self._read_operands_from_types(types_byte)

        info = self.EXTENDED.get(ext_opnum, (f"ext_{ext_opnum:02x}", False, False))
        name, has_store, has_branch = info

        store_var = None
        if has_store:
            store_var = self.read_byte(self.pc)
            self.pc += 1

        branch = None
        if has_branch:
            branch = self._read_branch()

        return name, operands, store_var, branch, None

    def _do_branch(self, condition: bool, branch_info: Tuple[int, bool]) -> None:
        """Execute branch based on condition"""
        offset, branch_on_true = branch_info
        if condition == branch_on_true:
            if offset == 0:
                self._return(0)
            elif offset == 1:
                self._return(1)
            else:
                self.pc = self.pc + offset - 2

    def _call_routine(self, packed_addr: int, args: List[int], store_var: Optional[int]) -> None:
        """Call a routine"""
        if packed_addr == 0:
            if store_var is not None:
                self.set_variable(store_var, 0)
            return

        routine_addr = self.unpack_address(packed_addr)
        num_locals = self.read_byte(routine_addr)
        routine_addr += 1

        # Save call frame
        frame = CallFrame(
            return_pc=self.pc,
            locals=list(self.locals),
            num_locals=num_locals,
            store_var=store_var,
            stack_depth=len(self.stack)
        )
        self.call_stack.append(frame)

        # Initialize locals
        self.locals = [0] * 16
        if self.header.version <= 4:
            # V1-4: locals have default values in routine header
            for i in range(num_locals):
                self.locals[i] = self.read_word(routine_addr)
                routine_addr += 2

        # Copy arguments to locals
        for i, arg in enumerate(args[:num_locals]):
            self.locals[i] = arg

        self.pc = routine_addr

    def _return(self, value: int) -> None:
        """Return from routine"""
        if not self.call_stack:
            self.finished = True
            self.running = False
            return

        frame = self.call_stack.pop()
        self.pc = frame.return_pc
        self.locals = frame.locals

        # Restore stack
        while len(self.stack) > frame.stack_depth:
            self.stack.pop()

        if frame.store_var is not None:
            self.set_variable(frame.store_var, value)

    def _signed(self, val: int) -> int:
        """Convert unsigned 16-bit to signed"""
        if val > 32767:
            return val - 65536
        return val

    def step(self) -> bool:
        """
        Execute one instruction.
        Returns True if execution should continue, False if waiting for input or finished.
        """
        if self.finished or self.waiting_for_input:
            return False

        self.instruction_count += 1
        name, operands, store_var, branch, text = self.decode_instruction()

        if self.debug:
            print(f"[{self.instruction_count}] {name} {operands} store={store_var} branch={branch}")

        # Get operand values
        ops = [self.get_operand(op) for op in operands]

        # Execute opcode
        if name == "rtrue":
            self._return(1)

        elif name == "rfalse":
            self._return(0)

        elif name == "print":
            self.print_text(text)

        elif name == "print_ret":
            self.print_text(text)
            self.print_text("\n")
            self._return(1)

        elif name == "nop":
            pass

        elif name == "restart":
            self.restart()

        elif name == "ret_popped":
            self._return(self.pop())

        elif name == "pop":
            self.pop()

        elif name == "quit":
            self.finished = True
            self.running = False

        elif name == "new_line":
            self.print_text("\n")

        elif name == "show_status":
            pass  # Ignore for now

        elif name == "verify":
            self._do_branch(True, branch)  # Always succeed

        elif name == "piracy":
            self._do_branch(True, branch)  # Always succeed

        # 1OP
        elif name == "jz":
            self._do_branch(ops[0] == 0, branch)

        elif name == "get_sibling":
            sibling = self.get_object_sibling(ops[0])
            self.set_variable(store_var, sibling)
            self._do_branch(sibling != 0, branch)

        elif name == "get_child":
            child = self.get_object_child(ops[0])
            self.set_variable(store_var, child)
            self._do_branch(child != 0, branch)

        elif name == "get_parent":
            self.set_variable(store_var, self.get_object_parent(ops[0]))

        elif name == "get_prop_len":
            self.set_variable(store_var, self.get_property_len(ops[0]))

        elif name == "inc":
            var_num = operands[0][1] if isinstance(operands[0], tuple) else operands[0]
            val = self._signed(self.get_variable(var_num)) + 1
            self.set_variable(var_num, val & 0xFFFF)

        elif name == "dec":
            var_num = operands[0][1] if isinstance(operands[0], tuple) else operands[0]
            val = self._signed(self.get_variable(var_num)) - 1
            self.set_variable(var_num, val & 0xFFFF)

        elif name == "print_addr":
            self.print_addr(ops[0])

        elif name == "call_1s":
            self._call_routine(ops[0], [], store_var)

        elif name == "remove_obj":
            self.remove_object(ops[0])

        elif name == "print_obj":
            self.print_object(ops[0])

        elif name == "ret":
            self._return(ops[0])

        elif name == "jump":
            offset = self._signed(ops[0])
            self.pc = self.pc + offset - 2

        elif name == "print_paddr":
            self.print_paddr(ops[0])

        elif name == "load":
            var_num = operands[0][1] if isinstance(operands[0], tuple) else operands[0]
            val = self.get_variable(var_num)
            # For var 0 (stack), we need to peek not pop
            if var_num == 0 and self.stack:
                val = self.stack[-1]
            self.set_variable(store_var, val)

        elif name == "call_1n":
            self._call_routine(ops[0], [], None)

        elif name == "not":
            # V1-4 only (V5+ uses call_1n)
            self.set_variable(store_var, (~ops[0]) & 0xFFFF)

        # 2OP
        elif name == "je":
            result = any(ops[0] == op for op in ops[1:])
            self._do_branch(result, branch)

        elif name == "jl":
            self._do_branch(self._signed(ops[0]) < self._signed(ops[1]), branch)

        elif name == "jg":
            self._do_branch(self._signed(ops[0]) > self._signed(ops[1]), branch)

        elif name == "dec_chk":
            var_num = operands[0][1] if isinstance(operands[0], tuple) else operands[0]
            val = self._signed(self.get_variable(var_num)) - 1
            self.set_variable(var_num, val & 0xFFFF)
            self._do_branch(val < self._signed(ops[1]), branch)

        elif name == "inc_chk":
            var_num = operands[0][1] if isinstance(operands[0], tuple) else operands[0]
            val = self._signed(self.get_variable(var_num)) + 1
            self.set_variable(var_num, val & 0xFFFF)
            self._do_branch(val > self._signed(ops[1]), branch)

        elif name == "jin":
            self._do_branch(self.get_object_parent(ops[0]) == ops[1], branch)

        elif name == "test":
            self._do_branch((ops[0] & ops[1]) == ops[1], branch)

        elif name == "or":
            self.set_variable(store_var, ops[0] | ops[1])

        elif name == "and":
            self.set_variable(store_var, ops[0] & ops[1])

        elif name == "test_attr":
            self._do_branch(self.get_attribute(ops[0], ops[1]), branch)

        elif name == "set_attr":
            self.set_attribute(ops[0], ops[1])

        elif name == "clear_attr":
            self.clear_attribute(ops[0], ops[1])

        elif name == "store":
            var_num = operands[0][1] if isinstance(operands[0], tuple) else operands[0]
            self.set_variable(var_num, ops[1])

        elif name == "insert_obj":
            self.insert_object(ops[0], ops[1])

        elif name == "loadw":
            addr = ops[0] + 2 * ops[1]
            self.set_variable(store_var, self.read_word(addr))

        elif name == "loadb":
            addr = ops[0] + ops[1]
            self.set_variable(store_var, self.read_byte(addr))

        elif name == "get_prop":
            self.set_variable(store_var, self.get_property(ops[0], ops[1]))

        elif name == "get_prop_addr":
            self.set_variable(store_var, self.get_property_addr(ops[0], ops[1]))

        elif name == "get_next_prop":
            self.set_variable(store_var, self.get_next_property(ops[0], ops[1]))

        elif name == "add":
            self.set_variable(store_var, (self._signed(ops[0]) + self._signed(ops[1])) & 0xFFFF)

        elif name == "sub":
            self.set_variable(store_var, (self._signed(ops[0]) - self._signed(ops[1])) & 0xFFFF)

        elif name == "mul":
            self.set_variable(store_var, (self._signed(ops[0]) * self._signed(ops[1])) & 0xFFFF)

        elif name == "div":
            if ops[1] == 0:
                raise ZMachineError("Division by zero")
            result = int(self._signed(ops[0]) / self._signed(ops[1]))
            self.set_variable(store_var, result & 0xFFFF)

        elif name == "mod":
            if ops[1] == 0:
                raise ZMachineError("Modulo by zero")
            a, b = self._signed(ops[0]), self._signed(ops[1])
            result = a - int(a / b) * b
            self.set_variable(store_var, result & 0xFFFF)

        elif name == "call_2s":
            self._call_routine(ops[0], [ops[1]], store_var)

        elif name == "call_2n":
            self._call_routine(ops[0], [ops[1]], None)

        elif name == "set_colour":
            pass  # Ignore

        # VAR
        elif name == "call" or name == "call_vs":
            args = ops[1:] if len(ops) > 1 else []
            self._call_routine(ops[0], args, store_var)

        elif name == "call_vs2":
            args = ops[1:] if len(ops) > 1 else []
            self._call_routine(ops[0], args, store_var)

        elif name == "call_vn":
            args = ops[1:] if len(ops) > 1 else []
            self._call_routine(ops[0], args, None)

        elif name == "call_vn2":
            args = ops[1:] if len(ops) > 1 else []
            self._call_routine(ops[0], args, None)

        elif name == "storew":
            self.write_word(ops[0] + 2 * ops[1], ops[2])

        elif name == "storeb":
            self.write_byte(ops[0] + ops[1], ops[2])

        elif name == "put_prop":
            self.put_property(ops[0], ops[1], ops[2])

        elif name == "sread" or name == "aread" or name == "read":
            # Input instruction - pause execution
            self.waiting_for_input = True
            text_buffer = ops[0]
            parse_buffer = ops[1] if len(ops) > 1 else 0

            def handle_input(input_text: str):
                self._process_input(input_text, text_buffer, parse_buffer)
                if store_var is not None and self.header.version >= 5:
                    # V5+ returns terminating character (13 for newline)
                    self.set_variable(store_var, 13)
                self.waiting_for_input = False
                self.pending_input_callback = None

            self.pending_input_callback = handle_input
            return False

        elif name == "print_char":
            self.print_char(ops[0])

        elif name == "print_num":
            self.print_num(ops[0])

        elif name == "random":
            n = self._signed(ops[0])
            if n <= 0:
                self.rng.seed(abs(n) if n < 0 else None)
                self.set_variable(store_var, 0)
            else:
                self.set_variable(store_var, self.rng.randint(1, n))

        elif name == "push":
            self.push(ops[0])

        elif name == "pull":
            var_num = operands[0][1] if isinstance(operands[0], tuple) else operands[0]
            self.set_variable(var_num, self.pop())

        elif name == "split_window":
            pass  # Ignore

        elif name == "set_window":
            pass  # Ignore

        elif name == "erase_window":
            pass  # Ignore

        elif name == "erase_line":
            pass  # Ignore

        elif name == "set_cursor":
            pass  # Ignore

        elif name == "get_cursor":
            pass  # Ignore

        elif name == "set_text_style":
            pass  # Ignore

        elif name == "buffer_mode":
            pass  # Ignore

        elif name == "output_stream":
            pass  # Ignore

        elif name == "input_stream":
            pass  # Ignore

        elif name == "sound_effect":
            pass  # Ignore

        elif name == "read_char":
            self.waiting_for_input = True

            def handle_char(input_text: str):
                char = ord(input_text[0]) if input_text else 13
                self.set_variable(store_var, char)
                self.waiting_for_input = False
                self.pending_input_callback = None

            self.pending_input_callback = handle_char
            return False

        elif name == "scan_table":
            x = ops[0]
            table = ops[1]
            length = ops[2]
            form = ops[3] if len(ops) > 3 else 0x82

            entry_size = form & 0x7F
            is_word = bool(form & 0x80)

            found_addr = 0
            for i in range(length):
                entry_addr = table + i * entry_size
                if is_word:
                    val = self.read_word(entry_addr)
                else:
                    val = self.read_byte(entry_addr)
                if val == x:
                    found_addr = entry_addr
                    break

            self.set_variable(store_var, found_addr)
            self._do_branch(found_addr != 0, branch)

        elif name == "tokenise":
            text_buf = ops[0]
            parse_buf = ops[1]
            self._tokenise(text_buf, parse_buf)

        elif name == "copy_table":
            first = ops[0]
            second = ops[1]
            size = self._signed(ops[2])

            if second == 0:
                # Zero out first table
                for i in range(abs(size)):
                    self.write_byte(first + i, 0)
            elif size > 0:
                # Copy forward (may overlap)
                for i in range(size):
                    self.write_byte(second + i, self.read_byte(first + i))
            else:
                # Copy backward
                size = abs(size)
                for i in range(size - 1, -1, -1):
                    self.write_byte(second + i, self.read_byte(first + i))

        elif name == "print_table":
            addr = ops[0]
            width = ops[1]
            height = ops[2] if len(ops) > 2 else 1
            skip = ops[3] if len(ops) > 3 else 0

            for row in range(height):
                for col in range(width):
                    self.print_char(self.read_byte(addr + row * (width + skip) + col))
                if row < height - 1:
                    self.print_text("\n")

        elif name == "check_arg_count":
            # Check if argument N was provided
            frame = self.call_stack[-1] if self.call_stack else None
            if frame:
                self._do_branch(ops[0] <= frame.num_locals, branch)
            else:
                self._do_branch(False, branch)

        # Extended
        elif name == "save":
            # For automated walking, always succeed
            self.set_variable(store_var, 1)

        elif name == "restore":
            # For automated walking, always fail (no saved game to restore)
            self.set_variable(store_var, 0)

        elif name == "save_undo":
            self.set_variable(store_var, 1)  # Success (but we don't actually save)

        elif name == "restore_undo":
            self.set_variable(store_var, 0)  # Fail

        elif name == "log_shift":
            val = ops[0]
            shift = self._signed(ops[1])
            if shift > 0:
                result = (val << shift) & 0xFFFF
            else:
                result = val >> (-shift)
            self.set_variable(store_var, result)

        elif name == "art_shift":
            val = self._signed(ops[0])
            shift = self._signed(ops[1])
            if shift > 0:
                result = (val << shift) & 0xFFFF
            else:
                result = val >> (-shift)
            self.set_variable(store_var, result & 0xFFFF)

        elif name == "set_font":
            self.set_variable(store_var, 1)  # Return previous font

        elif name == "print_unicode":
            self.print_char(ops[0])

        elif name == "check_unicode":
            self.set_variable(store_var, 3)  # Can print and read

        else:
            if self.debug:
                print(f"Unknown opcode: {name}")

        return True

    def _process_input(self, text: str, text_buffer: int, parse_buffer: int) -> None:
        """Process player input into text and parse buffers"""
        text = text.lower()[:self.read_byte(text_buffer)]

        if self.header.version <= 4:
            # V1-4: Store length in byte 1, text starts at byte 2
            for i, c in enumerate(text):
                self.write_byte(text_buffer + 1 + i, ord(c))
            self.write_byte(text_buffer + 1 + len(text), 0)
        else:
            # V5+: Byte 0 is max, byte 1 is actual length, text at byte 2
            self.write_byte(text_buffer + 1, len(text))
            for i, c in enumerate(text):
                self.write_byte(text_buffer + 2 + i, ord(c))

        if parse_buffer:
            self._tokenise(text_buffer, parse_buffer)

    def _tokenise(self, text_buffer: int, parse_buffer: int) -> None:
        """Tokenise text buffer into parse buffer"""
        # Read text from buffer
        if self.header.version <= 4:
            text_start = text_buffer + 1
            text = ""
            i = 0
            while True:
                c = self.read_byte(text_start + i)
                if c == 0:
                    break
                text += chr(c)
                i += 1
        else:
            text_len = self.read_byte(text_buffer + 1)
            text_start = text_buffer + 2
            text = "".join(chr(self.read_byte(text_start + i)) for i in range(text_len))

        # Get dictionary info
        dict_addr = self.header.dictionary
        num_seps = self.read_byte(dict_addr)
        separators = [chr(self.read_byte(dict_addr + 1 + i)) for i in range(num_seps)]
        dict_addr += 1 + num_seps

        entry_len = self.read_byte(dict_addr)
        dict_addr += 1
        num_entries = struct.unpack('>h', bytes(self.memory[dict_addr:dict_addr+2]))[0]
        dict_addr += 2

        # Tokenise
        words = []
        word_start = 0
        i = 0
        while i < len(text):
            c = text[i]
            if c == ' ':
                if i > word_start:
                    words.append((text[word_start:i], word_start))
                word_start = i + 1
            elif c in separators:
                if i > word_start:
                    words.append((text[word_start:i], word_start))
                words.append((c, i))
                word_start = i + 1
            i += 1

        if word_start < len(text):
            words.append((text[word_start:], word_start))

        # Write parse buffer
        max_words = self.read_byte(parse_buffer)
        self.write_byte(parse_buffer + 1, min(len(words), max_words))

        parse_addr = parse_buffer + 2
        for word, pos in words[:max_words]:
            # Look up word in dictionary
            dict_entry = self._lookup_word(word, dict_addr, entry_len, abs(num_entries))
            self.write_word(parse_addr, dict_entry)
            self.write_byte(parse_addr + 2, len(word))
            if self.header.version <= 4:
                self.write_byte(parse_addr + 3, pos + 1)  # 1-based position
            else:
                self.write_byte(parse_addr + 3, pos + 2)  # Offset from buffer start
            parse_addr += 4

    def _lookup_word(self, word: str, dict_start: int, entry_len: int, num_entries: int) -> int:
        """Look up word in dictionary, return address or 0 if not found"""
        # Encode word for comparison
        encoded = self._encode_word(word)

        # Binary search
        lo, hi = 0, num_entries - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            entry_addr = dict_start + mid * entry_len

            # Compare encoded bytes
            cmp = 0
            for i in range(len(encoded)):
                dict_byte = self.read_byte(entry_addr + i)
                if encoded[i] < dict_byte:
                    cmp = -1
                    break
                elif encoded[i] > dict_byte:
                    cmp = 1
                    break

            if cmp == 0:
                return entry_addr
            elif cmp < 0:
                hi = mid - 1
            else:
                lo = mid + 1

        return 0

    def _encode_word(self, word: str) -> bytes:
        """Encode word for dictionary lookup"""
        # Z-character encoding
        word = word.lower()
        max_chars = 6 if self.header.version <= 3 else 9
        word = word[:max_chars]

        zchars = []
        for c in word:
            if c in self.A0:
                zchars.append(self.A0.index(c) + 6)
            elif c in self.A1:
                zchars.append(4)  # Shift to A1
                zchars.append(self.A1.index(c) + 6)
            else:
                # A2 character or special
                a2 = " \n0123456789.,!?_#'\"/\\-:()"
                if c in a2:
                    zchars.append(5)  # Shift to A2
                    zchars.append(a2.index(c) + 6)

        # Pad with 5s (shift to A2, but no character follows = padding)
        while len(zchars) < max_chars:
            zchars.append(5)

        # Pack into bytes
        num_words = 2 if self.header.version <= 3 else 3
        result = []
        for i in range(num_words):
            base = i * 3
            if base + 2 < len(zchars):
                word_val = (zchars[base] << 10) | (zchars[base + 1] << 5) | zchars[base + 2]
            elif base + 1 < len(zchars):
                word_val = (zchars[base] << 10) | (zchars[base + 1] << 5) | 5
            elif base < len(zchars):
                word_val = (zchars[base] << 10) | (5 << 5) | 5
            else:
                word_val = (5 << 10) | (5 << 5) | 5

            if i == num_words - 1:
                word_val |= 0x8000  # Set end bit

            result.append((word_val >> 8) & 0xFF)
            result.append(word_val & 0xFF)

        return bytes(result)

    def run(self, max_steps: int = 1000000) -> None:
        """Run until input needed or finished"""
        self.running = True
        steps = 0
        while steps < max_steps:
            if not self.step():
                break
            steps += 1
        self.running = False

    def send_input(self, text: str) -> None:
        """Send input to waiting game"""
        if self.waiting_for_input and self.pending_input_callback:
            self.pending_input_callback(text)

    def get_output(self) -> str:
        """Get and clear output buffer"""
        output = self.output_buffer
        self.output_buffer = ""
        return output
