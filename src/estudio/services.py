import shutil
import os

ATTACHMENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "attachments",
)


def store_attachment_file(origen):
    if not origen or not os.path.exists(origen):
        return None
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    destino = os.path.join(ATTACHMENTS_DIR, os.path.basename(origen))
    shutil.copy2(origen, destino)
    return destino
