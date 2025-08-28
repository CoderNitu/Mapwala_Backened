# accounts/management/commands/seed_rbac.py
from accounts.models import Capability, Role, State
from django.core.management.base import BaseCommand

DEFAULT_CAPS = [
    ("user.create", "Create users"),
    ("user.list", "List users"),
    ("user.view", "View user"),
    ("user.update", "Update user"),
    ("user.delete", "Delete user"),
    ("user.change_manager", "Change user manager"),
    ("purchase.create", "Create purchase order"),
    ("purchase.approve", "Approve purchase order"),
    ("sales.create", "Create sales order"),
    ("sales.approve", "Approve sales order"),
    ("bom.upload", "Upload BOM"),
    ("batch.inspect", "Inspect batch (QE)"),
]

ROLE_MAP = {
    "admin": {"name": "Admin", "caps": [c[0] for c in DEFAULT_CAPS]},
    "subadmin": {
        "name": "Subadmin",
        "caps": [
            "user.list",
            "user.view",
            "user.update",
            "bom.upload",
            "purchase.create",
        ],
    },
    "gm": {
        "name": "GM / Manager",
        "caps": [
            "user.list",
            "user.view",
            "user.change_manager",
            "purchase.approve",
            "sales.approve",
        ],
    },
    "sales": {"name": "Sales Executive", "caps": ["sales.create", "user.view"]},
    "purchase": {
        "name": "Purchase Executive",
        "caps": ["purchase.create", "user.view"],
    },
    "qe": {"name": "Quality Engineer", "caps": ["batch.inspect", "user.view"]},
    "manufacturer": {"name": "Manufacturer", "caps": ["bom.upload", "user.view"]},
    "buyer": {"name": "Buyer", "caps": ["purchase.create", "user.view"]},
    "dealer": {"name": "Dealer", "caps": ["sales.create", "user.view"]},
    "accounts": {
        "name": "Accounts",
        "caps": ["sales.approve", "purchase.approve", "user.view"],
    },
    "sales": {"name": "Sales", "caps": ["sales.create", "sales.approve", "user.view"]},
}

DEFAULT_STATES = [
    "Assam" ,
    "Maharashtra",
    "Karnataka",
    "Tamil Nadu",
    "Delhi",
    "Gujarat",
    "West Bengal",
]


class Command(BaseCommand):
    help = "Seed default capabilities, roles, and states for custom RBAC"

    def handle(self, *args, **options):
        # 🔹 Capabilities
        created_caps = []
        for code, desc in DEFAULT_CAPS:
            cap, _ = Capability.objects.get_or_create(
                code=code, defaults={"description": desc}
            )
            created_caps.append(cap.code)

        # 🔹 Roles
        created_roles = []
        for key, meta in ROLE_MAP.items():
            role, _ = Role.objects.get_or_create(
                key=key, defaults={"name": meta["name"]}
            )
            caps_qs = Capability.objects.filter(code__in=meta["caps"])
            role.capabilities.set(caps_qs)
            created_roles.append(role.key)

        # 🔹 States
        created_states = []
        for state_name in DEFAULT_STATES:
            state, _ = State.objects.get_or_create(name=state_name)
            created_states.append(state.name)

        self.stdout.write(
            self.style.SUCCESS(f"Created capabilities: {', '.join(created_caps)}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created roles: {', '.join(created_roles)}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created states: {', '.join(created_states)}")
        )
