import os

NOTIFICATIONS_EMAIL = 'notifications@performance.service.gov.uk'
NO_REPLY_EMAIL = 'performance@performance.service.gov.uk'

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

ROLES = [
    {
        "role": "dashboard-editor",
        "features": [
            "edit-dashboards"
        ],
    },
    {
        "role": "admin",
        "features": [
            "edit-dashboards",
            "big-edit",
        ],
    },
]
