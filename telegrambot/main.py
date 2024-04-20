import asyncio
from functionalities import commands_gestion_main, awake_conv_main, asleep_conv_main

async def main():
    await asyncio.gather(
        commands_gestion_main(),
        awake_conv_main(),
        asleep_conv_main()
    )

if __name__ == "__main__":
    asyncio.run(main())

