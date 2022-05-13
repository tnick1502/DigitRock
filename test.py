import asyncio

async def get_pages(site_name):
    await asyncio.sleep(1)
    print(f"get pages for {site_name}")
    return range(1, 4)

async def get_pages_data(site_name, page):
    await asyncio.sleep(1)
    return f"data from page {page}, ({site_name})"

async def get(site_name):
    pages = await get_pages(site_name)
    for page in pages:
        data = await get_pages_data(site_name, page)
        print(data)

async def main():
    tasks = []
    for i in ["site_1", "site_2", "site_3"]:
        tasks.append(asyncio.create_task(get(i)))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
