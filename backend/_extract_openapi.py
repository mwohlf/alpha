import asyncio

async def main():
    # your logic to print app.openapi()
    import yaml
    from main import app
    print(yaml.dump(app.openapi()))

if __name__ == "__main__":
    asyncio.run(main())