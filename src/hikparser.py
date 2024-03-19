"""
HIKVISION Video Data Recovery
Author: Dane Wullen
Date: 2020
Version: 0.1
NO WARRANTY, SOFWARE IS PROVIDED 'AS IS'


© 2020 Dane Wullen
"""



from .hikpageentry import HikPageEntry
from .hikbtree import HikBTree
from .hikmastersector import HikMasterSector
from .hikdatablockentry import HikDataBlockEntry
from bitstring import ConstBitStream
import struct
import datetime
import logging


import datetime
import hashlib

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')


class HikParser(Exception):

    def to_bit(self, byte):
        return byte * 8

    def set_pos(self, pos):
        # self.data.pos = self.to_bit(pos)
        self.file_obj.seek(pos)

    def get_pos(self):
        # return self.to_bit(self.data.pos)
        return self.file_obj.tell()

    def read_bytes(self, num_bytes):
        # self.file_obj = open(self.disk_name, 'rb')
        return self.file_obj.read(num_bytes)

    def close(self):
        self.file_obj.close()

    def skip_bytes(self, offset):
        # self.data.pos += self.to_bit(offset)
        self.file_obj.seek(offset, 1)

    def __init__(self, filename):
        self.disk_name = filename
        try:
            self.file_obj = open(self.disk_name, 'rb')  # Sử dụng biến khác cho file object
        except Exception as e:
            logging.error(f"Error opening physical drive {self.disk_name}: {e}")
            raise
        self.master_sector = HikMasterSector()
        self.hikbtree = HikBTree()
        self.hikbtree.page_list = []


    def __str__(self):
        return str(self.master_sector) + "\n" + str(self.hikbtree) + "\n" + str(self.hikpagelist)

    def get_total_blocks(self):
        total = 0
        for page in self.hikbtree.get_page_list():
            total += len(page.data_blocks)

        return total

    def hex_to_string(self, hex):
        return bytes.fromhex(str(hex)[2:])

    def hex_to_ascii(self, hex):
        return bytes.fromhex(str(hex)[2:]).decode("ASCII").strip(' \t\n\r')

    def read_master_sector(self):
        self.file_obj.read(528)
        # self.set_pos(528)
        signature_data = self.read_bytes(32)
        self.master_sector.signatur = self.hex_to_ascii(signature_data)
        logging.info(f"signature_data {self.master_sector.signatur}")
        if not self.master_sector.check_signatur():
            raise Exception('SignatureException: Signature not equal to HIKVISION@HANGZHOU!')
        self.skip_bytes(24)
        hdd_cap_data = self.read_bytes(8)
        self.master_sector.hdd_cap = struct.unpack('<Q', hdd_cap_data)[0]  # Sử dụng 'Q' cho unsigned long long (uint64)

        self.skip_bytes(16)
        sys_log_offset_data = self.read_bytes(8)
        self.master_sector.sys_log_offset = struct.unpack('<Q', sys_log_offset_data)[0]

        sys_log_size_data = self.read_bytes(8)
        self.master_sector.sys_log_size = struct.unpack('<Q', sys_log_size_data)[0]

        self.skip_bytes(8)
        video_data_area_offset_data = self.read_bytes(8)
        self.master_sector.video_data_area_offset = struct.unpack('<Q', video_data_area_offset_data)[0]

        self.skip_bytes(8)
        data_block_size_data = self.read_bytes(8)
        self.master_sector.data_block_size = struct.unpack('<Q', data_block_size_data)[0]

        data_block_total_data = self.read_bytes(4)
        self.master_sector.data_block_total = struct.unpack('<I', data_block_total_data)[0]  # Sử dụng 'I' cho unsigned int (uint32)

        self.skip_bytes(4)
        hikbtree1_offset_data = self.read_bytes(8)
        self.master_sector.hikbtree1_offset = struct.unpack('<Q', hikbtree1_offset_data)[0]

        hikbtree1_size_data = self.read_bytes(4)
        self.master_sector.hikbtree1_size = struct.unpack('<I', hikbtree1_size_data)[0]

        self.skip_bytes(4)
        hikbtree2_offset_data = self.read_bytes(8)
        self.master_sector.hikbtree2_offset = struct.unpack('<Q', hikbtree2_offset_data)[0]

        hikbtree2_size_data = self.read_bytes(4)
        self.master_sector.hikbtree2_size = struct.unpack('<I', hikbtree2_size_data)[0]

        self.skip_bytes(60)
        init_time_data = self.read_bytes(4)
        init_time = struct.unpack('<I', init_time_data)[0]
        self.master_sector.init_time = datetime.datetime.fromtimestamp(init_time).strftime('%d.%m.%Y %H:%M:%S'),
        logging.info("End read master")
    # def read_master_sector(self):
    #     """
    #        Reads master sector of HIKVISION systems and write its content into class.
    #        Initial position should always be Offset 528 Byte.
    #     """

    #     self.set_pos(528)
    #     self.master_sector.signatur = self.hex_to_ascii(self.data.read(self.to_bit(32)))
    #     if not self.master_sector.check_signatur():
    #         raise Exception('SignatureException: Signature not equal to HIKVISION@HANGZHOU!')

    #     self.skip_bytes(24)
    #     self.master_sector.hdd_cap = self.data.read('uintle:64')
    #     self.skip_bytes(16)
    #     self.master_sector.sys_log_offset = self.data.read('uintle:64')
    #     self.master_sector.sys_log_size = self.data.read('uintle:64')
    #     self.skip_bytes(8)
    #     self.master_sector.video_data_area_offset = self.data.read('uintle:64')
    #     self.skip_bytes(8)
    #     self.master_sector.data_block_size = self.data.read('uintle:64')
    #     self.master_sector.data_block_total = self.data.read('uintle:32')
    #     self.skip_bytes(4)
    #     self.master_sector.hikbtree1_offset = self.data.read('uintle:64')
    #     self.master_sector.hikbtree1_size = self.data.read('uintle:32')
    #     self.skip_bytes(4)
    #     self.master_sector.hikbtree2_offset = self.data.read('uintle:64')
    #     self.master_sector.hikbtree2_size = self.data.read('uintle:32')
    #     self.skip_bytes(60)
    #     # UTC Timestamp
    #     self.master_sector.init_time = datetime.datetime.fromtimestamp(self.data.read('uintle:32'))\
    #                                        .strftime('%d.%m.%Y %H:%M:%S'),

    def read_hikbtree(self):
        """
        Reads the first of the two HIKBTrees and writes to class.
        Initial offset for HIKBTree is located in master sector.
        """
        self.set_pos(self.master_sector.hikbtree1_offset)

        # Skip 16 unused bytes
        self.skip_bytes(16)

        signature_data = self.read_bytes(8)
        self.hikbtree.signatur = self.hex_to_ascii(signature_data)

        self.skip_bytes(36)

        created_time_data = self.read_bytes(4)
        created_time = struct.unpack('<I', created_time_data)[0]
        self.hikbtree.created_time = datetime.datetime.fromtimestamp(created_time).strftime('%d.%m.%Y %H:%M:%S'),

        footer_offset_data = self.read_bytes(8)
        self.hikbtree.footer_offset = struct.unpack('<Q', footer_offset_data)[0]

        self.skip_bytes(8)

        page_list_offset_data = self.read_bytes(8)
        self.hikbtree.page_list_offset = struct.unpack('<Q', page_list_offset_data)[0]

        page_one_offset_data = self.read_bytes(8)
        self.hikbtree.page_one_offset = struct.unpack('<Q', page_one_offset_data)[0]
    # def read_hikbtree(self):
    #     """
    #         Reads the first of the two HISBTREES and writes to class.
    #         Initial offset for HIBKTREE is located in master sector.
    #     """

    #     self.set_pos(self.master_sector.hikbtree1_offset)
    #     # Skip 16 unused bytes
    #     self.skip_bytes(16)
    #     self.hikbtree.signatur = self.hex_to_ascii(self.data.read(self.to_bit(8)))
    #     self.skip_bytes(36)
    #     self.hikbtree.created_time = datetime.datetime.fromtimestamp(self.data.read('uintle:32'))\
    #         .strftime('%d.%m.%Y %H:%M:%S'),
    #     self.hikbtree.footer_offset = self.data.read('uintle:64')
    #     self.skip_bytes(8)
    #     self.hikbtree.page_list_offset = self.data.read('uintle:64')
    #     self.hikbtree.page_one_offset = self.data.read('uintle:64')

    def read_page_list(self):
        """ Reads page list page for page and writes content into list."""
        
        self.set_pos(self.hikbtree.page_list_offset)
        self.skip_bytes(24)
        first_page_offset_data = self.read_bytes(8)
        first_page_offset = struct.unpack('<Q', first_page_offset_data)[0]
        
        self.skip_bytes(64)  # Đã bao gồm 64 bytes cần bỏ qua thay vì bỏ qua 96 bytes tổng cộng
        
        page_offset_data = self.read_bytes(8)
        page_offset = struct.unpack('<Q', page_offset_data)[0]
        
        # Add first page to entries
        page = HikPageEntry()
        page.offset_to_page = first_page_offset
        page.data_blocks = []
        self.hikbtree.add_hikpage(page)
        
        while page_offset != 0:
            self.set_pos(page_offset)
            
            page = HikPageEntry()
            page.offset_to_page = page_offset
            
            channel_data = self.read_bytes(2)
            page.channel = struct.unpack('<H', channel_data)[0]  # Giả định là unsigned short (2 bytes)
            
            self.skip_bytes(6)  # Điều chỉnh tùy thuộc vào cấu trúc dữ liệu
            
            start_time_data = self.read_bytes(4)
            page.start_time = struct.unpack('<I', start_time_data)[0]  # unsigned int
            
            end_time_data = self.read_bytes(4)
            page.end_time = struct.unpack('<I', end_time_data)[0]  # unsigned int
            
            data_offset_data = self.read_bytes(8)
            page.data_offset = struct.unpack('<Q', data_offset_data)[0]
            
            page.data_blocks = []
            self.hikbtree.add_hikpage(page)
            
            # Đọc offset của trang tiếp theo
            page_offset_data = self.read_bytes(8)
            page_offset = struct.unpack('<Q', page_offset_data)[0]
    # def read_page_list(self):
    #     """ Reads page list page for page and writes content into list."""

    #     # The first page is not listed in the pagelist, we have to put it in manually

    #     self.set_pos(self.hikbtree.page_list_offset)
    #     self.skip_bytes(24)
    #     first_page_offset = self.data.read('uintle:64')
    #     self.skip_bytes(64)
    #     # self.skip_bytes(96)
    #     page_offset = self.data.read('uintle:64')

    #     # Add first page to entries
    #     page = HikPageEntry()
    #     page.offset_to_page = first_page_offset
    #     page.data_blocks = []
    #     self.hikbtree.add_hikpage(page)

    #     while page_offset != 0:
    #         page = HikPageEntry()
    #         page.offset_to_page = page_offset
    #         self.skip_bytes(8)
    #         page.channel = self.data.read(self.to_bit(2))
    #         self.skip_bytes(6)
    #         page.start_time = self.data.read('uintle:32')
    #         page.end_time = self.data.read('uintle:32')
    #         page.data_offset = self.data.read('uintle:64')
    #         page.data_blocks = []
    #         self.hikbtree.add_hikpage(page)
    #         self.skip_bytes(8)
    #         page_offset = self.data.read('uintle:64')

    def read_page_entries(self):
        for page in self.hikbtree.get_page_list():
            self.set_pos(page.offset_to_page + 96)  # Bỏ qua 96 bytes đầu tiên của mỗi trang

            while True:
                # Đọc 8 bytes tiếp theo và kiểm tra xem chúng có phải là bytes không sử dụng hay không
                unused_bytes_data = self.read_bytes(8)
                unused_bytes = struct.unpack('<Q', unused_bytes_data)[0]
                
                if unused_bytes == 0xFFFFFFFFFFFFFFFF:  # Kết thúc các mục dữ liệu nếu gặp bytes không sử dụng
                    break

                # Đọc thông tin về mỗi data block
                existence_of_file_data = self.read_bytes(8)
                existence_of_file = struct.unpack('<Q', existence_of_file_data)[0]
                
                channel_data = self.read_bytes(2)
                channel = struct.unpack('<H', channel_data)[0]  # Giả sử channel là unsigned short (2 bytes)

                self.skip_bytes(6)  # Bỏ qua bytes không cần thiết giữa các trường

                start_time_data = self.read_bytes(4)
                start_time = struct.unpack('<I', start_time_data)[0]  # unsigned int
                
                end_time_data = self.read_bytes(4)
                end_time = struct.unpack('<I', end_time_data)[0]  # unsigned int
                
                data_offset_data = self.read_bytes(8)
                data_offset = struct.unpack('<Q', data_offset_data)[0]  # unsigned long long

                # Thêm data block vào trang
                data_block = HikDataBlockEntry()
                data_block.existence_of_file = existence_of_file
                data_block.channel = channel
                data_block.start_time = start_time
                data_block.end_time = end_time
                data_block.data_offset = data_offset
                page.data_blocks.append(data_block)

                # Đọc 8 bytes tiếp theo để chuẩn bị cho lần lặp tiếp theo
                # Lưu ý: Nếu có bất kỳ dữ liệu padding hoặc bổ sung nào giữa các data block, bạn cần skip chính xác số byte đó
    # def read_page_entries(self):
    #     for page in self.hikbtree.get_page_list():
    #         self.set_pos(page.offset_to_page)
    #         self.skip_bytes(96)
    #         unused_bytes = self.data.read('uintle:64')
    #         # Same as zu 0xFFFFFFFFFFFFFFFF
    #         while unused_bytes == 18446744073709551615:
    #             data_block = HikDataBlockEntry()
    #             data_block.existence_of_file = self.data.read('uintle:64')
    #             data_block.channel = self.data.read(self.to_bit(2))
    #             self.skip_bytes(6)
    #             data_block.start_time = self.data.read('uintle:32')
    #             data_block.end_time = self.data.read('uintle:32')
    #             data_block.data_offset = self.data.read('uintle:64')
    #             page.data_blocks.append(data_block)
    #             self.skip_bytes(8)
    #             unused_bytes = self.data.read('uintle:64')

    def extract_block(self, dir):
        i = 1
        for page in self.hikbtree.get_page_list():
            j = 1
            for datablock in page.data_blocks:
                length = self.master_sector.data_block_size
                with open(self.file_obj, 'rb') as f1:
                    f1.seek(datablock.data_offset)
                    fileName = dir + "\\" + datetime.datetime.utcfromtimestamp(datablock.start_time).strftime(
                        '%Y-%m-%d_%H-%M-%S') + "-" + \
                               datetime.datetime.utcfromtimestamp(datablock.end_time).strftime('%Y-%m-%d_%H-%M-%S') + \
                               "_ch_" + str(int.from_bytes(self.hex_to_string(datablock.channel), byteorder="big")) + \
                               "_id_" + str(j)

                    fileNameMD5 = fileName + ".md5"
                    fileName = fileName + ".mp4"

                    md5Hash = hashlib.md5()
                    with open(fileName, 'wb') as f2:
                        while length:
                            chunk = min(1024 * 1024, length)
                            data = f1.read(chunk)
                            f2.write(data)
                            length -= chunk
                            md5Hash.update(data)
                        print("Block {} of page {} extracted!".format(j, i))
                    with open (fileNameMD5, 'w') as f3:
                        f3.write(md5Hash.hexdigest())
                    f2.close()
                    f3.close()
                    j += 1
                f1.close()
            i += 1

    def print_hikpagelist(self, dir):
        with open(dir + "\\HIKPageList.csv", "w", newline="") as file:
            i = 1
            file.write("Page;Channel;Starttime;Endtime;Offset\n")
            for page in self.hikbtree.get_page_list():
                output = "{};{};{};{};{}".format(
                    str(i),
                    int.from_bytes(self.hex_to_string(page.channel), byteorder="big"),
                    datetime.datetime.utcfromtimestamp(page.start_time).strftime('%d.%m.%Y %H:%M:%S'),
                    datetime.datetime.utcfromtimestamp(page.end_time).strftime('%d.%m.%Y %H:%M:%S'),
                    page.offset_to_page
                )
                file.write(output + "\n")
                i += 1
        file.close()

    def print_hikbtree(self, dir):
        with open(dir + "\\HIKBTree.txt", "w", newline="") as file:
            file.write("Signature: {}\n".format(self.hikbtree.signatur))
            file.write("Creation date: {}\n".format(self.hikbtree.created_time))
            file.write("Offset to footer: {}\n".format(self.hikbtree.footer_offset))
            file.write("Offset to page list: {}\n".format(self.hikbtree.page_list_offset))
            file.write("Offset to first page: {}\n".format(self.hikbtree.page_one_offset))
        file.close()

    def print_hikpages(self, dir):
        with open(dir + "\\HIKPages.csv", "w", newline="") as file:
            i = 1
            file.write("Page;Datablock;Channel;Starttime;Endtime;Offset\n")
            for page_entry in self.hikbtree.get_page_list():
                j = 1
                for page in page_entry.data_blocks:
                    output = "{};{};{};{};{};{}".format(
                        str(i),
                        str(j),
                        int.from_bytes(self.hex_to_string(page.channel), byteorder="big"),
                        datetime.datetime.utcfromtimestamp(page.start_time).strftime('%d.%m.%Y %H:%M:%S'),
                        datetime.datetime.utcfromtimestamp(page.end_time).strftime('%d.%m.%Y %H:%M:%S'),
                        page.data_offset
                    )
                    file.write(output + "\n")
                    j += 1
                j = 0
                i += 1
        file.close()

    def print_master_sector(self, dir):
        with open(dir + "\\HIKMasterSector.txt", "w", newline="") as file:
            file.write("Signature: {}\n".format(self.master_sector.signatur))
            file.write("Hard disk size: {}\n".format(self.master_sector.hdd_cap))
            file.write("Offset to system logs: {}\n".format(self.master_sector.sys_log_offset))
            file.write("System log size: {}\n".format(self.master_sector.sys_log_size))
            file.write("Offset to video data area: {}\n".format(self.master_sector.video_data_area_offset))
            file.write("data block size: {}\n".format(self.master_sector.data_block_size))
            file.write("Total data blocks: {}\n".format(self.master_sector.data_block_total))
            file.write("Offset to HIKBTree 1: {}\n".format(self.master_sector.hikbtree1_offset))
            file.write("Size of HIKBTree 1: {}\n".format(self.master_sector.hikbtree1_size))
            file.write("Offset to HIKBTree 2: {}\n".format(self.master_sector.hikbtree2_offset))
            file.write("Size of HIKBTree 2: {}\n".format(self.master_sector.hikbtree2_size))
            file.write("Creation date: {}\n".format(self.master_sector.init_time))
        file.close()





