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
    all_data =[]
    for page in pages:
        data = await get_pages_data(site_name, page)
        all_data.append(data)
    return all_data

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    tasks = []
    for i in ["site_1", "site_2", "site_3"]:
        tasks.append(asyncio.ensure_future(get(i)))

    res = loop.run_until_complete(asyncio.gather(*tasks))
    print(res)
    loop.close()
