import asyncio

def run_async(func):
    loop = asyncio.get_event_loop()
    task = loop.create_task(func)
    loop.run_until_complete(asyncio.gather(task))
    return task.result()
