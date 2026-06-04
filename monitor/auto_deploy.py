import shutil

from .config import DASHBOARD_PATH, DATA_PATH, DEPLOY_DIR, logger


def auto_deploy() -> bool:
    """Prepare the GitHub Pages publish directory."""
    try:
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        targets = [
            (DASHBOARD_PATH, DEPLOY_DIR / "index.html"),
            (DATA_PATH, DEPLOY_DIR / "data.json"),
        ]
        copied = 0
        for src, dst in targets:
            if src.exists():
                shutil.copy2(src, dst)
                copied += 1
                logger.info("Deploy file synced: %s -> %s", src, dst)
            else:
                logger.warning("Deploy source missing: %s", src)
        (DEPLOY_DIR / ".nojekyll").write_text("", encoding="utf-8")
        return copied == len(targets)
    except Exception as exc:
        logger.warning("Deploy sync error: %s", exc)
        return False
