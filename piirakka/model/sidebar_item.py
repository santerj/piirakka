from dataclasses import dataclass, asdict

# App sidebar items. This data is not dynamic (not queried from API), so pydantic is not needed.

@dataclass
class SidebarItem:
    name: str
    url: str
    icon: str

sidebar_items = [asdict(SidebarItem(**item)) for item in [
        {'name': 'home', 'url': '/', 'icon': 'static/icons/home-2-line.svg'},
        {'name': 'manage stations', 'url': '/stations', 'icon': 'static/icons/rfid-line.svg'},
        {'name': 'settings', 'url': '/settings', 'icon': 'static/icons/settings-4-line.svg'}
    ]
]
