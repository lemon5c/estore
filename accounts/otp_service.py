"""
OTP sending service.
Supports: console (dev), whatsapp (CallMeBot), sms (stub).
"""
import urllib.parse
import urllib.request
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp(phone: str, code: str, channel: str = "whatsapp") -> bool:
    """
    Send OTP to given phone number via the specified channel.
    Returns True on success, False on failure.
    """
    backend = getattr(settings, "OTP_BACKEND", "console")

    if backend == "console":
        return _send_console(phone, code)
    elif backend == "whatsapp" or channel == "whatsapp":
        return _send_whatsapp_callmebot(phone, code)
    elif backend == "sms" or channel == "sms":
        return _send_sms_stub(phone, code)
    else:
        logger.warning(f"Unknown OTP backend: {backend}")
        return _send_console(phone, code)


def _send_console(phone: str, code: str) -> bool:
    """Print OTP to console — for development."""
    print(f"\n{'='*40}")
    print(f"  OTP CODE for {phone}: {code}")
    print(f"{'='*40}\n")
    logger.info(f"[CONSOLE OTP] {phone} → {code}")
    return True


def _send_whatsapp_callmebot(phone: str, code: str) -> bool:
    """
    Send OTP via CallMeBot WhatsApp API.
    Note: The recipient must have added the CallMeBot contact first.
    For OTPs to customers, this requires them to opt-in to CallMeBot.
    For owner notifications, use the owner's registered number.
    """
    api_key = getattr(settings, "CALLMEBOT_OWNER_API_KEY", "")
    if not api_key:
        logger.error("CALLMEBOT_OWNER_API_KEY not configured")
        return _send_console(phone, code)

    message = f"Your verification code is: {code}\nDo not share this with anyone."
    encoded_msg = urllib.parse.quote(message)
    encoded_phone = urllib.parse.quote(phone)
    url = f"https://api.callmebot.com/whatsapp.php?phone={encoded_phone}&text={encoded_msg}&apikey={api_key}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            result = response.read().decode()
            logger.info(f"CallMeBot response for {phone}: {result}")
            return True
    except Exception as e:
        logger.error(f"CallMeBot send failed for {phone}: {e}")
        return False


def _send_sms_stub(phone: str, code: str) -> bool:
    """
    SMS stub — replace with actual Libyan SMS provider integration.
    e.g., Almadar/Libyana SMS gateway.
    """
    logger.warning(f"[SMS STUB] Would send OTP {code} to {phone} via SMS")
    print(f"\n[SMS STUB] OTP {code} → {phone}\n")
    return True


def notify_owner_new_order(order) -> bool:
    """
    Send WhatsApp notification to the store owner about a new order.
    Uses CallMeBot with the owner's registered phone+apikey.
    """
    phone = getattr(settings, "CALLMEBOT_OWNER_PHONE", "")
    api_key = getattr(settings, "CALLMEBOT_OWNER_API_KEY", "")

    if not phone or not api_key:
        logger.warning("Owner WhatsApp notification not configured")
        return False

    # Build order summary
    items_text = ""
    for item in order.items.select_related("variant__product"):
        items_text += f"\n  - {item.variant.product.name}"
        opts = item.variant.options_display()
        if opts:
            items_text += f" ({opts})"
        items_text += f" x{item.quantity} @ {item.price_at_order} LYD"

    message = (
        f"🛒 New Order #{order.id}\n"
        f"Customer: {order.user.get_full_name()}\n"
        f"Phone: {order.user.phone}\n"
        f"Items:{items_text}\n"
        f"Total: {order.total_price()} LYD\n"
        f"Notes: {order.notes or 'None'}"
    )

    encoded_msg = urllib.parse.quote(message)
    encoded_phone = urllib.parse.quote(phone)
    url = f"https://api.callmebot.com/whatsapp.php?phone={encoded_phone}&text={encoded_msg}&apikey={api_key}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            result = response.read().decode()
            logger.info(f"Owner order notification sent: {result}")
            return True
    except Exception as e:
        logger.error(f"Owner notification failed: {e}")
        return False
