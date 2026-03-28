import asyncio


async def scheduler_loop(notify_service):
    while True:
        try:
            await notify_service.process_notifications()
        except Exception as e:
            print(f"[Scheduler Error]: {e}")

        await asyncio.sleep(30)