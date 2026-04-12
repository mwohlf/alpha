import asyncio


async def main():
    import yaml
    from main import app

    print(yaml.dump(app.openapi()))


if __name__ == "__main__":
    asyncio.run(main())
