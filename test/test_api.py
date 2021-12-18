import asyncio

from pypedrive_api.api import Client
from pypedrive_api.objects import LeadLabel, LeadColor


async def main():
    async with Client() as client:
        lead_label = LeadLabel(name="From App", color=LeadColor.blue)
        await client.create_lead_label(lead_label)


if __name__ == "__main__":
    asyncio.run(main())
