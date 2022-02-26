__version__ = '0.55.5'

__changelog__ = {
    "0.55.5": """
        - fix parsing club games during fetching owned games; extend logging for unparsable items
    """,
    "0.55.4": """
        - hotfix fetching club games by replacing version of API endpoint
    """,
    "0.55.3": """
        - changed login window's title
        - replaced deprecated owned games endpoint
        - fix problem with doubled gametimes for some games (eg. Trackmania, Division 2)
        - remove +1h gametime fix for For Honour as it is already fixed on Ubisoft side
        - round down gametime to full minutes to better reflect Ubisoft logic
    """,
    "0.55.2": """
        - bump galaxy.plugin.api version for more stable `get_local_size`
    """,
    "0.55.1": """
        - fix potential crashes due to blocking `get_local_size` method
    """
}
