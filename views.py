import discord
from price import PriceInfo
from models import PriceAlerts
import json

from wrappers import alert_check

class CreateAlertView(discord.ui.View):
    def __init__(self, info: PriceInfo):
        super().__init__()
        self.info = info

    @discord.ui.button(label="Create Alert", style=discord.ButtonStyle.red)
    @alert_check()
    async def alert_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        modal = CreateAlertModal(self.info)
        await interaction.response.send_modal(modal=modal)


class CreateAlertModal(discord.ui.Modal):
    def __init__(self, info: PriceInfo):
        super().__init__(
            discord.ui.InputText(
                label="Target Price", placeholder="$20", min_length=1, max_length=4
            ),
            title="Price Alert",
        )
        self.info = info

    async def callback(self, interaction: discord.Interaction):
        price = self.children[0].value.replace("$", "")
        try:
            price = int(float(price))
            PriceAlerts.add_alert(
                interaction,
                game_name=self.info.game_name,
                image_url=self.info.image,
                price=price,
                game_plain=self.info.game_plain,
            )
            response = f"Price Alert for `{self.info.game_name}` created."
            await interaction.response.send_message(response)
        except ValueError:
            response = f"Target price must be a number. You input `{price}`."
            await interaction.response.send_message(response, ephemeral=True)


class PriceAlertDropdown(discord.ui.Select):
    """A dropdown with price alert options for the users server. Chosen option
    will be deleted."""

    def __init__(self, alerts: list[PriceAlerts]):

        # This creates a list of values along with options
        # to avoid duplicate options.
        options = []
        values = []
        for alert in alerts:
            label = f"{alert.game_name} under ${alert.price}"
            value = {
                "channel": alert.channel,
                "game_name": alert.game_name[0:10],
                "price": alert.price,
            }
            value = json.dumps(value)
            if value not in values:
                values.append(value)
                option = discord.SelectOption(label=label, value=value)
                options.append(option)
            else:
                continue

        super().__init__(
            placeholder="Choose an alert to delete.", min_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        from alerts import delete_server_alerts

        alert = json.loads(self.values[0])
        game_name = alert["game_name"]
        channel = alert["channel"]
        price = alert["price"]
        delete_server_alerts(
            interaction.guild.id,
            PriceAlerts,
            game_name=game_name,
            channel=channel,
            price=price,
        )
        response = f"Price alert deleted."
        await interaction.response.send_message(response)


class VoteButton(discord.ui.View):
    def __init__(self):
        url = "https://top.gg/bot/1028073862597967932/vote"
        super().__init__(discord.ui.Button(label="Vote to Enter", url=url))
