import asyncio
import os

from pypedrive_async.api import Client
from pypedrive_async.objects import LeadColor, LeadLabel


async def main():
    async with Client(os.environ.get("PIPEDRIVE_API_KEY"), os.environ.get("PIPEDRIVE_URL", ""), "App") as client:
        # await client.create_minimal_lead("minimal4@example.com", LeadLabel(name="app: signed up", color=LeadColor.purple))
        await client.add_label_to_minimal_lead("minimal4@example.com", LeadLabel(name="app: uploaded document", color=LeadColor.gray))


if __name__ == "__main__":
    asyncio.run(main())
