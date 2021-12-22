import asyncio

from pypedrive_api.api import Client
from pypedrive_api.objects import LeadColor, LeadLabel


async def main():
    async with Client(..., ..., ...) as client:
        await client.create_minimal_lead("minimal3@example.com", LeadLabel(name="app: signed up", color=LeadColor.purple))
        await client.add_label_to_minimal_lead("minimal3@example.com", LeadLabel(name="app: uploaded document", color=LeadColor.gray))


if __name__ == "__main__":
    asyncio.run(main())
