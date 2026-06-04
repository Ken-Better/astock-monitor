"""Copy dashboard + data.json to deploy folder for Netlify"""
import shutil
from .config import BASE_DIR, logger

def auto_deploy():
    """Copy outputs (dashboard.html + data.json) to deploy/ for GitHub Actions deployment."""
    try:
        src_html = BASE_DIR / "outputs" / "dashboard.html"
        dst_html = BASE_DIR / "deploy" / "index.html"
        src_data = BASE_DIR / "outputs" / "data.json"
        dst_data = BASE_DIR / "deploy" / "data.json"

        copied = []
        if src_html.exists():
            shutil.copy2(str(src_html), str(dst_html))
            copied.append("index.html")
        if src_data.exists():
            shutil.copy2(str(src_data), str(dst_data))
            copied.append("data.json")

        if copied:
            logger.info(f"Deploy files synced: {', '.join(copied)}")
            return True
        else:
            logger.warning("No files to deploy")
            return False
    except Exception as e:
        logger.warning(f"Deploy sync error: {e}")
        return False
