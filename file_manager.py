import aiofiles
from aiocsv import AsyncWriter, AsyncReader
from prettytable import PrettyTable


class File_Manager:

    def __init__(self, file_name, payload_path):

        self.result_file_name = file_name
        self.path_to_payloads = payload_path

    table_header = ["Method", "URL", "First Time Load", "Second Time Load", "Cache-control", "Expires", "ETag",
                    "Last-Modified"]

    async def sort_file(self):
        """
        Sorting of crawling results
        """
        read_rows = await self.read_from_file(self.result_file_name)
        await self.write_to_file(mode='w', row=self.table_header)
        await self.write_to_file(rows=sorted(read_rows[1:], key=lambda x: float(x[2]), reverse=True))

    async def write_to_file(self, mode='a', rows=None, row=None):
        async with aiofiles.open(self.result_file_name, mode=mode, encoding="UTF-8", newline="") as afp:
            writer = AsyncWriter(afp, dialect="unix")
            if rows:
                await writer.writerows(rows)
            elif row:
                await writer.writerow(row)

    async def show_in_terminal(self):
        """
        Print the first 50 sorted crawl results
        """
        read_rows = await self.read_from_file(self.result_file_name)
        p_table = PrettyTable()
        p_table.field_names = read_rows[0][1:4]
        for row in read_rows[1:51]:
            p_table.add_row(row[1:4])
        if len(read_rows) >= 50:
            print('Too many rows to show')
        print(p_table[:50])

    async def read_from_file(self, file_name):

        """
        Send request to URL and get page load time

        Parameters
        --------------

            file_name : str,
                Path to crawl results

        Returns
        ------------
            list[List[str]]

        """

        async with aiofiles.open(file_name, mode="r", encoding="UTF-8", newline="") as afp:
            read_rows = [i async for i in AsyncReader(afp, dialect='unix')]
            return read_rows
