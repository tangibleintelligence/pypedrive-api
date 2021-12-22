import asyncio

from pypedrive_api.api import Client
from pypedrive_api.objects import LeadColor, LeadLabel


async def main():
    async with Client("2800bf239dc735be297f65e2412b3c94ba576b27", "https://ti-sandbox.pipedrive.com", "App") as client:
        # await client.create_minimal_lead("minimal4@example.com", LeadLabel(name="app: signed up", color=LeadColor.purple))
        await client.add_label_to_minimal_lead("minimal4@example.com", LeadLabel(name="app: uploaded document", color=LeadColor.gray))


if __name__ == "__main__":
    asyncio.run(main())
