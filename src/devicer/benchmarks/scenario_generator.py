from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from data_generator import (
    create_base_fingerprint,
    create_attractor_fingerprint,
    _TIMEZONES,
    _SCREEN_RESOLUTIONS,
    _CHROME_VERSIONS,
    _simple_hash,
)


@dataclass(frozen=True)
class ScenarioMetadata:
    """Metadata describing a test scenario"""
    scenario_type: str  # e.g., "BrowserDrift/Minor"
    expected_match: bool  # Ground truth: should these match?
    difficulty: str  # "easy" | "medium" | "hard" | "extreme"
    description: str  # Human-readable explanation


@dataclass(frozen=True)
class ScenarioPair:
    """A pair of fingerprints with scenario metadata"""
    fp1: Dict[str, Any]
    fp2: Dict[str, Any]
    metadata: ScenarioMetadata
    device_id: str  # Identifier for tracking

def _generate_browser_drift_minor(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Minor version bump (Chrome 120.0.1 → 120.0.2)"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Extract current version from userAgent
    ua = str(fp2.get("userAgent", ""))
    if "Chrome/" in ua:
        parts = ua.split("Chrome/")
        if len(parts) > 1:
            version_part = parts[1].split()[0]
            version_nums = version_part.split(".")
            if len(version_nums) >= 3:
                # Bump patch version
                version_nums[2] = str(int(version_nums[2]) + random.randint(1, 3))
                new_version = ".".join(version_nums)
                fp2["userAgent"] = ua.replace(version_part, new_version)
                
                # Update appVersion too
                if "appVersion" in fp2:
                    fp2["appVersion"] = fp2["appVersion"].replace(version_part, new_version)
    
    # Minor canvas variation (browser update can slightly affect rendering)
    if "canvas" in fp2:
        fp2["canvas"] = _simple_hash(str(fp2["canvas"]) + str(random.randint(0, 5)))
    
    metadata = ScenarioMetadata(
        scenario_type="BrowserDrift/Minor",
        expected_match=True,
        difficulty="easy",
        description="Same device, minor browser patch update"
    )
    
    return fp1, fp2, metadata


def _generate_browser_drift_major(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Major version jump (Chrome 120 → 125)"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Major version bump
    ua = str(fp2.get("userAgent", ""))
    if "Chrome/" in ua:
        parts = ua.split("Chrome/")
        if len(parts) > 1:
            version_part = parts[1].split()[0]
            version_nums = version_part.split(".")
            if len(version_nums) >= 1:
                # Jump major version
                current_major = int(version_nums[0])
                new_major = current_major + random.randint(3, 8)
                version_nums[0] = str(new_major)
                new_version = ".".join(version_nums)
                fp2["userAgent"] = ua.replace(version_part, new_version)
                
                if "appVersion" in fp2:
                    fp2["appVersion"] = fp2["appVersion"].replace(version_part, new_version)
    
    # Moderate canvas variation
    if "canvas" in fp2:
        fp2["canvas"] = _simple_hash(str(fp2["canvas"]) + str(random.randint(0, 999)))
    
    # Font list might change slightly with browser update
    if "fonts" in fp2 and isinstance(fp2["fonts"], list):
        if len(fp2["fonts"]) > 2 and random.random() < 0.3:
            fp2["fonts"] = fp2["fonts"][:-1]  # Remove one font
        elif random.random() < 0.2:
            # Add a new system font that wasn't detected before
            new_fonts = ["Segoe UI Variable", "Yu Gothic UI", "MS UI Gothic"]
            fp2["fonts"].append(random.choice(new_fonts))
    
    metadata = ScenarioMetadata(
        scenario_type="BrowserDrift/Major",
        expected_match=True,
        difficulty="medium",
        description="Same device, major browser version jump"
    )
    
    return fp1, fp2, metadata


def _generate_browser_drift_cross(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Cross-browser: Same device, Chrome → Firefox or Safari"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Keep hardware/screen same, change browser signatures
    platform = fp2.get("platform", "Win32")
    
    if "Mac" in platform:
        # Switch to Safari
        fp2["userAgent"] = f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        fp2["vendor"] = "Apple Computer, Inc."
        fp2["productSub"] = "20030107"
    else:
        # Switch to Firefox
        ff_version = random.choice([115, 120, 122, 125])
        os_part = fp2.get("userAgent", "").split(")")[0] + ")"
        fp2["userAgent"] = f"Mozilla/5.0 {os_part}; rv:{ff_version}.0) Gecko/20100101 Firefox/{ff_version}.0"
        fp2["vendor"] = ""
        fp2["productSub"] = "20100101"
    
    # Canvas/WebGL will be completely different
    if "canvas" in fp2:
        fp2["canvas"] = _simple_hash(str(fp2["canvas"]) + "firefox_engine" + str(random.randint(0, 999999)))
    if "webgl" in fp2:
        fp2["webgl"] = _simple_hash(str(fp2["webgl"]) + "different_renderer" + str(random.randint(0, 999999)))
    
    # Different plugin handling
    fp2["plugins"] = []
    fp2["mimeTypes"] = []
    
    metadata = ScenarioMetadata(
        scenario_type="BrowserDrift/CrossBrowser",
        expected_match=True,
        difficulty="hard",
        description="Same device, different browser (Chrome ↔ Firefox/Safari)"
    )
    
    return fp1, fp2, metadata


def _generate_environment_home_office(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Home ↔ Office: different screen resolution, timezone stays same"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Change screen resolution (office might have different monitor)
    if "screen" in fp2:
        current_res = (fp2["screen"].get("width", 1920), fp2["screen"].get("height", 1080))
        available_res = [r for r in _SCREEN_RESOLUTIONS if r != current_res]
        new_w, new_h = random.choice(available_res)
        fp2["screen"]["width"] = new_w
        fp2["screen"]["height"] = new_h
    
    # Minor canvas variation due to resolution change
    if "canvas" in fp2:
        fp2["canvas"] = _simple_hash(str(fp2["canvas"]) + str(random.randint(0, 50)))
    
    metadata = ScenarioMetadata(
        scenario_type="EnvironmentChange/HomeOffice",
        expected_match=True,
        difficulty="easy",
        description="Same user/device, different location (home vs office monitor)"
    )
    
    return fp1, fp2, metadata


def _generate_environment_dock_external(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Laptop docked with external monitor vs standalone"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Docked: much larger resolution
    if "screen" in fp2:
        # Jump to 4K or ultrawide
        large_resolutions = [(2560, 1440), (3440, 1440), (3840, 2160)]
        new_w, new_h = random.choice(large_resolutions)
        fp2["screen"]["width"] = new_w
        fp2["screen"]["height"] = new_h
    
    metadata = ScenarioMetadata(
        scenario_type="EnvironmentChange/DockExternal",
        expected_match=True,
        difficulty="medium",
        description="Laptop docked with external monitor"
    )
    
    return fp1, fp2, metadata


def _generate_environment_mobile_desktop(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Same user, different devices (mobile vs desktop)"""
    # This should NOT match - different devices entirely
    fp1 = copy.deepcopy(base_fp)
    
    # Create a completely different device for the same "user"
    fp2 = create_base_fingerprint(random.randint(1, 999999))
    
    # But keep timezone same (same user, same location)
    fp2["timezone"] = fp1.get("timezone", "America/New_York")
    fp2["language"] = fp1.get("language", "en-US")
    
    metadata = ScenarioMetadata(
        scenario_type="EnvironmentChange/MobileDesktop",
        expected_match=False,  # Different devices!
        difficulty="medium",
        description="Same user, different devices (mobile vs desktop)"
    )
    
    return fp1, fp2, metadata



def _generate_privacy_tor_browser(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Tor Browser Bundle - unified fingerprints"""
    # Two different users with Tor Browser look identical
    
    # Tor Browser standard fingerprint
    tor_fp = {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
        "platform": "Win32",
        "timezone": "UTC",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "cookieEnabled": True,
        "doNotTrack": False,
        "product": "Gecko",
        "productSub": "20100101",
        "vendor": "",
        "vendorSub": "",
        "appName": "Netscape",
        "appVersion": "5.0 (Windows)",
        "appCodeName": "Mozilla",
        "hardwareConcurrency": 8,  # Spoofed
        "deviceMemory": 8,  # Spoofed
        "screen": {
            "width": 1920,
            "height": 1080,
            "colorDepth": 24,
            "pixelDepth": 24,
            "orientation": {"type": "landscape-primary", "angle": 0},
        },
        "fonts": ["Arial", "Times New Roman", "Courier New"],  # Minimal set
        "plugins": [],
        "mimeTypes": [],
        "canvas": _simple_hash("tor_browser_canvas_unified"),
        "webgl": _simple_hash("tor_browser_webgl_blocked"),
        "audio": _simple_hash("tor_browser_audio_blocked"),
    }
    
    fp1 = copy.deepcopy(tor_fp)
    fp2 = copy.deepcopy(tor_fp)
    
    metadata = ScenarioMetadata(
        scenario_type="PrivacyHardening/TorBrowser",
        expected_match=False,  # Different users, but look identical!
        difficulty="extreme",
        description="Two different Tor Browser users (unified fingerprints)"
    )
    
    return fp1, fp2, metadata


def _generate_privacy_resist_fingerprinting(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Firefox resist fingerprinting mode - same device, limited info"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Strip high-entropy fields
    fp2.pop("canvas", None)
    fp2.pop("webgl", None)
    fp2.pop("audio", None)
    
    # Reduce fonts to minimal set
    fp2["fonts"] = ["Arial", "Times New Roman", "Courier New"]
    
    # Round screen resolution
    if "screen" in fp2:
        fp2["screen"]["width"] = 1920
        fp2["screen"]["height"] = 1080
    
    # Spoof hardware
    fp2["hardwareConcurrency"] = 8
    fp2["deviceMemory"] = 8
    
    metadata = ScenarioMetadata(
        scenario_type="PrivacyHardening/ResistFingerprinting",
        expected_match=True,  # Same device, but privacy mode
        difficulty="hard",
        description="Same device, Firefox resist fingerprinting enabled"
    )
    
    return fp1, fp2, metadata


def _generate_privacy_canvas_defender(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Canvas defender extension - noise injection"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Canvas is completely randomized every session
    if "canvas" in fp2:
        fp2["canvas"] = _simple_hash(str(fp2["canvas"]) + "random_noise" + str(random.randint(0, 9999999)))
    
    # WebGL might also be affected
    if "webgl" in fp2 and random.random() < 0.5:
        fp2["webgl"] = _simple_hash(str(fp2["webgl"]) + str(random.randint(0, 99999)))
    
    metadata = ScenarioMetadata(
        scenario_type="PrivacyHardening/CanvasDefender",
        expected_match=True,  # Same device, extension adds noise
        difficulty="hard",
        description="Same device, canvas defender extension active"
    )
    
    return fp1, fp2, metadata



def _generate_adversarial_canvas_noise(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Random canvas/WebGL noise injection"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Completely randomize high-entropy fields
    if "canvas" in fp2:
        fp2["canvas"] = _simple_hash("adversarial_" + str(random.randint(0, 99999999)))
    if "webgl" in fp2:
        fp2["webgl"] = _simple_hash("adversarial_webgl_" + str(random.randint(0, 99999999)))
    if "audio" in fp2:
        fp2["audio"] = _simple_hash("adversarial_audio_" + str(random.randint(0, 99999999)))
    
    metadata = ScenarioMetadata(
        scenario_type="AdversarialPerturbation/CanvasNoise",
        expected_match=True,  # Same device, but trying to evade
        difficulty="extreme",
        description="Same device, adversarial noise injection on canvas/WebGL"
    )
    
    return fp1, fp2, metadata


def _generate_adversarial_font_randomization(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Font list randomization while keeping hardware same"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Completely randomize font list
    all_fonts = ["Arial", "Helvetica", "Times", "Courier", "Verdana", "Georgia", 
                 "Comic Sans MS", "Trebuchet MS", "Impact", "Palatino", "Garamond",
                 "Bookman", "Avant Garde", "Century", "Monaco", "Optima"]
    random.shuffle(all_fonts)
    fp2["fonts"] = all_fonts[:random.randint(8, 15)]
    
    metadata = ScenarioMetadata(
        scenario_type="AdversarialPerturbation/FontRandomization",
        expected_match=True,
        difficulty="hard",
        description="Same device, font list randomized to evade detection"
    )
    
    return fp1, fp2, metadata


def _generate_adversarial_ua_rotation(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """UserAgent rotation with fixed hardware"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Keep hardware same, rotate UA
    fake_uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]
    fp2["userAgent"] = random.choice(fake_uas)
    
    # But canvas/webgl stay the same (hardware is same)
    # This creates a mismatch: UA says Mac, but canvas signature is Windows
    
    metadata = ScenarioMetadata(
        scenario_type="AdversarialPerturbation/UARotation",
        expected_match=True,
        difficulty="hard",
        description="Same device, UserAgent spoofed but hardware signatures remain"
    )
    
    return fp1, fp2, metadata



def _generate_mobility_timezone_travel(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """User traveled: timezone changed"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Change timezone (travel from US to Europe or Asia)
    current_tz = fp2.get("timezone", "America/New_York")
    if "America" in current_tz:
        # Travel to Europe or Asia
        new_tz = random.choice(["Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai"])
    else:
        # Travel to US
        new_tz = random.choice(["America/New_York", "America/Los_Angeles"])
    
    fp2["timezone"] = new_tz
    
    metadata = ScenarioMetadata(
        scenario_type="MobilityChurn/TimezoneTravel",
        expected_match=True,
        difficulty="easy",
        description="Same device, user traveled (timezone changed)"
    )
    
    return fp1, fp2, metadata


def _generate_mobility_vpn_activation(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """VPN activated: timezone might change, but device same"""
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # VPN might change reported timezone
    if random.random() < 0.5:
        fp2["timezone"] = random.choice(_TIMEZONES)
    
    # Some VPNs inject headers or modify minor things
    if random.random() < 0.3 and "canvas" in fp2:
        fp2["canvas"] = _simple_hash(str(fp2["canvas"]) + str(random.randint(0, 10)))
    
    metadata = ScenarioMetadata(
        scenario_type="MobilityChurn/VPNActivation",
        expected_match=True,
        difficulty="medium",
        description="Same device, VPN activated (timezone may change)"
    )
    
    return fp1, fp2, metadata


def _generate_commodity_corporate_fleet(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Corporate laptop fleet: same model, same OS image"""
    # Two different users with identical corporate laptops
    
    corporate_fp = {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "platform": "Win32",
        "timezone": "America/New_York",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "cookieEnabled": True,
        "doNotTrack": False,
        "product": "Gecko",
        "productSub": "20100101",
        "vendor": "Google Inc.",
        "vendorSub": "",
        "appName": "Netscape",
        "appVersion": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "appCodeName": "Mozilla",
        "hardwareConcurrency": 8,
        "deviceMemory": 16,
        "screen": {
            "width": 1920,
            "height": 1080,
            "colorDepth": 24,
            "pixelDepth": 24,
            "orientation": {"type": "landscape-primary", "angle": 0},
        },
        "fonts": ["Arial", "Calibri", "Cambria", "Consolas", "Georgia", "Segoe UI", "Times New Roman", "Verdana"],
        "plugins": [{"name": "Chrome PDF Viewer", "description": "Portable Document Format"}],
        "mimeTypes": [{"type": "application/pdf", "description": "Portable Document Format", "suffixes": "pdf"}],
    }
    
    fp1 = copy.deepcopy(corporate_fp)
    fp2 = copy.deepcopy(corporate_fp)
    
    # Only difference: canvas/webgl/audio (actual hardware rendering)
    fp1["canvas"] = _simple_hash("corp_device_001_" + str(random.randint(0, 999)))
    fp1["webgl"] = _simple_hash("corp_webgl_001_" + str(random.randint(0, 999)))
    fp1["audio"] = _simple_hash("corp_audio_001_" + str(random.randint(0, 999)))
    
    fp2["canvas"] = _simple_hash("corp_device_002_" + str(random.randint(0, 999)))
    fp2["webgl"] = _simple_hash("corp_webgl_002_" + str(random.randint(0, 999)))
    fp2["audio"] = _simple_hash("corp_audio_002_" + str(random.randint(0, 999)))
    
    metadata = ScenarioMetadata(
        scenario_type="CommodityCollision/CorporateFleet",
        expected_match=False,  # Different users!
        difficulty="extreme",
        description="Different users, identical corporate laptops"
    )
    
    return fp1, fp2, metadata


def _generate_commodity_iphone_defaults(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """iPhone defaults: thousands of users with same config"""
    
    iphone_fp = {
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "platform": "iPhone",
        "timezone": "America/New_York",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "cookieEnabled": True,
        "doNotTrack": False,
        "product": "Gecko",
        "productSub": "20030107",
        "vendor": "Apple Computer, Inc.",
        "vendorSub": "",
        "appName": "Netscape",
        "appCodeName": "Mozilla",
        "hardwareConcurrency": 6,
        "deviceMemory": 8,
        "screen": {
            "width": 393,
            "height": 852,
            "colorDepth": 24,
            "pixelDepth": 24,
            "orientation": {"type": "portrait-primary", "angle": 0},
        },
        "fonts": ["Arial", "Helvetica", "Times New Roman"],
        "plugins": [],
        "mimeTypes": [],
    }
    
    fp1 = copy.deepcopy(iphone_fp)
    fp2 = copy.deepcopy(iphone_fp)
    
    # Slight canvas variations (but very similar)
    fp1["canvas"] = _simple_hash("iphone_canvas_" + str(random.randint(0, 999)))
    fp2["canvas"] = _simple_hash("iphone_canvas_" + str(random.randint(0, 999)))
    
    fp1["webgl"] = _simple_hash("iphone_webgl_A14")
    fp2["webgl"] = _simple_hash("iphone_webgl_A14")
    
    metadata = ScenarioMetadata(
        scenario_type="CommodityCollision/iPhoneDefaults",
        expected_match=False,  # Different users!
        difficulty="extreme",
        description="Different users, identical iPhone 14 Pro configurations"
    )
    
    return fp1, fp2, metadata


def _generate_commodity_public_terminal(base_fp: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], ScenarioMetadata]:
    """Public library/internet café terminal"""
    # Same physical device, different sessions/users
    
    fp1 = copy.deepcopy(base_fp)
    fp2 = copy.deepcopy(base_fp)
    
    # Device is the same, but session cleared between users
    # Canvas should be identical (same hardware)
    # This is actually the SAME device, different users
    
    metadata = ScenarioMetadata(
        scenario_type="CommodityCollision/PublicTerminal",
        expected_match=True,  # Same device, but different users!
        difficulty="extreme",
        description="Same physical device (library terminal), different users/sessions"
    )
    
    return fp1, fp2, metadata


# Scenario generator registry
SCENARIO_GENERATORS = {
    "BrowserDrift/Minor": _generate_browser_drift_minor,
    "BrowserDrift/Major": _generate_browser_drift_major,
    "BrowserDrift/CrossBrowser": _generate_browser_drift_cross,
    "EnvironmentChange/HomeOffice": _generate_environment_home_office,
    "EnvironmentChange/DockExternal": _generate_environment_dock_external,
    "EnvironmentChange/MobileDesktop": _generate_environment_mobile_desktop,
    "PrivacyHardening/TorBrowser": _generate_privacy_tor_browser,
    "PrivacyHardening/ResistFingerprinting": _generate_privacy_resist_fingerprinting,
    "PrivacyHardening/CanvasDefender": _generate_privacy_canvas_defender,
    "AdversarialPerturbation/CanvasNoise": _generate_adversarial_canvas_noise,
    "AdversarialPerturbation/FontRandomization": _generate_adversarial_font_randomization,
    "AdversarialPerturbation/UARotation": _generate_adversarial_ua_rotation,
    "MobilityChurn/TimezoneTravel": _generate_mobility_timezone_travel,
    "MobilityChurn/VPNActivation": _generate_mobility_vpn_activation,
    "CommodityCollision/CorporateFleet": _generate_commodity_corporate_fleet,
    "CommodityCollision/iPhoneDefaults": _generate_commodity_iphone_defaults,
    "CommodityCollision/PublicTerminal": _generate_commodity_public_terminal,
}


def generate_scenario_pair(
    scenario_type: str,
    base_fp: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None
) -> ScenarioPair:
    """
    Generate a scenario test pair
    
    Args:
        scenario_type: Type of scenario (e.g., "BrowserDrift/Minor")
        base_fp: Optional base fingerprint (will generate if not provided)
        seed: Optional random seed for reproducibility
    
    Returns:
        ScenarioPair with two fingerprints and metadata
    """
    if seed is not None:
        random.seed(seed)
    
    if scenario_type not in SCENARIO_GENERATORS:
        raise ValueError(f"Unknown scenario type: {scenario_type}. Available: {list(SCENARIO_GENERATORS.keys())}")
    
    # Generate base fingerprint if not provided
    if base_fp is None:
        base_fp = create_base_fingerprint(random.randint(1, 999999))
    
    # Generate the scenario pair
    generator = SCENARIO_GENERATORS[scenario_type]
    fp1, fp2, metadata = generator(base_fp)
    
    device_id = f"scenario_{scenario_type.replace('/', '_')}_{random.randint(1000, 9999)}"
    
    return ScenarioPair(
        fp1=fp1,
        fp2=fp2,
        metadata=metadata,
        device_id=device_id
    )


def generate_scenario_dataset(
    size: int,
    scenario_distribution: Optional[Dict[str, float]] = None
) -> List[ScenarioPair]:
    """
    Generate a balanced dataset across scenario types
    
    Args:
        size: Total number of scenario pairs to generate
        scenario_distribution: Optional dict mapping scenario types to proportions
                             (must sum to 1.0). If None, uses equal distribution.
    
    Returns:
        List of ScenarioPair objects
    """
    if scenario_distribution is None:
        # Equal distribution across all scenarios
        scenario_types = list(SCENARIO_GENERATORS.keys())
        proportion = 1.0 / len(scenario_types)
        scenario_distribution = {st: proportion for st in scenario_types}
    
    # Validate distribution
    total = sum(scenario_distribution.values())
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"Scenario distribution must sum to 1.0, got {total}")
    
    # Generate pairs
    pairs: List[ScenarioPair] = []
    
    for scenario_type, proportion in scenario_distribution.items():
        count = int(size * proportion)
        
        for _ in range(count):
            # Generate new base fingerprint for each pair
            base_fp = create_base_fingerprint(random.randint(1, 999999))
            pair = generate_scenario_pair(scenario_type, base_fp)
            pairs.append(pair)
    
    # Fill remaining to reach exact size
    while len(pairs) < size:
        scenario_type = random.choice(list(scenario_distribution.keys()))
        base_fp = create_base_fingerprint(random.randint(1, 999999))
        pair = generate_scenario_pair(scenario_type, base_fp)
        pairs.append(pair)
    
    random.shuffle(pairs)
    return pairs[:size]


def get_scenario_types() -> List[str]:
    """Get list of all available scenario types"""
    return list(SCENARIO_GENERATORS.keys())


def get_scenario_categories() -> Dict[str, List[str]]:
    """Get scenarios grouped by category"""
    categories: Dict[str, List[str]] = {}
    
    for scenario_type in SCENARIO_GENERATORS.keys():
        category = scenario_type.split("/")[0]
        categories.setdefault(category, []).append(scenario_type)
    
    return categories


import copy
from typing import Any, Dict, List

from scenario_generator import (
    generate_scenario_pair,
    generate_scenario_dataset,
    get_scenario_types,
    get_scenario_categories,
)
from data_generator import create_base_fingerprint
from metrics import ScoredPair, calculate_metrics, calculate_true_eer
from scoring_breakdown import decompose_confidence, format_breakdown


def _format_table(data: List[Dict[str, Any]]) -> str:
    if not data:
        return "(empty)\n"

    keys = list(data[0].keys())
    rows: List[List[str]] = []
    for row in data:
        values: List[str] = []
        for key in keys:
            val = row.get(key)
            values.append(f"{val:.3f}" if isinstance(val, float) else str(val))
        rows.append(values)

    col_widths = [max(len(keys[i]), *(len(row[i]) for row in rows)) for i in range(len(keys))]
    sep = "-|-".join("-" * width for width in col_widths)
    header = " | ".join(keys[i].ljust(col_widths[i]) for i in range(len(keys)))
    body = "\n".join(" | ".join(row[i].ljust(col_widths[i]) for i in range(len(keys))) for row in rows)
    return f"{header}\n{sep}\n{body}\n"


def _average(values: List[float]) -> float:
    return (sum(values) / len(values)) if values else 0.0


def _band(value: float, low_to_med: float, med_to_high: float) -> str:
    if value < low_to_med:
        return "low"
    if value < med_to_high:
        return "med"
    return "high"


def _expected_band_set(spec: str) -> set[str]:
    mapping = {
        "low": "low",
        "med": "med",
        "medium": "med",
        "high": "high",
    }
    tokens = [tok.strip().lower() for tok in spec.replace("-", "/").split("/") if tok.strip()]
    normalized = {mapping.get(tok, tok) for tok in tokens}
    return {tok for tok in normalized if tok in {"low", "med", "high"}}


def _band_matches(spec: str, observed: str) -> bool:
    expected = _expected_band_set(spec)
    return observed in expected if expected else False


def _as_metric_inputs(pairs: List[Dict[str, Any]], score_key: str) -> List[ScoredPair]:
    return [
        {
            "score": float(pair[score_key]),
            "sameDevice": bool(pair["sameDevice"]),
            "isAttractor": bool(pair["isAttractor"]),
        }
        for pair in pairs
    ]


def _sparsify_fingerprint(fp: Dict[str, Any]) -> Dict[str, Any]:
    keep_fields = [
        "userAgent",
        "platform",
        "timezone",
        "language",
        "languages",
        "hardwareConcurrency",
        "deviceMemory",
        "screen",
    ]
    sparse: Dict[str, Any] = {}
    for field in keep_fields:
        if field in fp:
            sparse[field] = copy.deepcopy(fp[field])
    return sparse


def demo_trust_semantics_truth_table():
    print("----\n")
    print("## Trust/Commonness Semantic Truth Table")

    # Fixed seeds keep this table stable across runs.
    tor_pair = generate_scenario_pair("PrivacyHardening/TorBrowser", seed=91001)
    corporate_pair = generate_scenario_pair("CommodityCollision/CorporateFleet", seed=91002)
    minor_pair = generate_scenario_pair("BrowserDrift/Minor", seed=91003)
    cross_pair = generate_scenario_pair("BrowserDrift/CrossBrowser", seed=91004)

    base_a = create_base_fingerprint(13579)
    base_b = create_base_fingerprint(24680)
    sparse_a = _sparsify_fingerprint(base_a)
    sparse_b = _sparsify_fingerprint(base_b)

    cases = [
        {
            "case": "Tor vs Tor (different users)",
            "fp1": tor_pair.fp1,
            "fp2": tor_pair.fp2,
            "expected_match": False,
            "should_commonness": "high",
            "should_distinctiveness": "low",
            "should_insufficiency": "low",
            "should_trust_adjustment": "high",
        },
        {
            "case": "Corporate fleet (different users)",
            "fp1": corporate_pair.fp1,
            "fp2": corporate_pair.fp2,
            "expected_match": False,
            "should_commonness": "high",
            "should_distinctiveness": "low",
            "should_insufficiency": "low",
            "should_trust_adjustment": "high",
        },
        {
            "case": "Minor drift (same device)",
            "fp1": minor_pair.fp1,
            "fp2": minor_pair.fp2,
            "expected_match": True,
            "should_commonness": "low/med",
            "should_distinctiveness": "med/high",
            "should_insufficiency": "low",
            "should_trust_adjustment": "low",
        },
        {
            "case": "Cross-browser (same device)",
            "fp1": cross_pair.fp1,
            "fp2": cross_pair.fp2,
            "expected_match": True,
            "should_commonness": "low/med",
            "should_distinctiveness": "med/high",
            "should_insufficiency": "low/med",
            "should_trust_adjustment": "low/med",
        },
        {
            "case": "Sparse fp (same device)",
            "fp1": base_a,
            "fp2": sparse_a,
            "expected_match": True,
            "should_commonness": "med/high",
            "should_distinctiveness": "low/med",
            "should_insufficiency": "high",
            "should_trust_adjustment": "med/high",
        },
        {
            "case": "Sparse fp (different device)",
            "fp1": sparse_a,
            "fp2": sparse_b,
            "expected_match": False,
            "should_commonness": "high",
            "should_distinctiveness": "low",
            "should_insufficiency": "high",
            "should_trust_adjustment": "med/high",
        },
    ]

    rows: List[Dict[str, Any]] = []
    for case in cases:
        breakdown = decompose_confidence(case["fp1"], case["fp2"], top_n=0)
        raw_same_device = breakdown.raw_profile_scores.get("same_device", breakdown.raw_similarity_score)
        final_same_device = breakdown.profile_scores.get("same_device", breakdown.overall_confidence)
        # Metric-aware bands:
        # - commonness/distinctiveness are 0-100 style.
        # - trust adjustment is in score points; values >20 are already substantial.
        commonness_band = _band(breakdown.commonness_score, low_to_med=40.0, med_to_high=70.0)
        distinctiveness_band = _band(breakdown.distinctiveness_score, low_to_med=40.0, med_to_high=70.0)
        insufficiency_band = _band(breakdown.insufficiency_risk, low_to_med=35.0, med_to_high=65.0)
        trust_band = _band(breakdown.trust_adjustment, low_to_med=8.0, med_to_high=20.0)

        commonness_ok = _band_matches(case["should_commonness"], commonness_band)
        distinctiveness_ok = _band_matches(case["should_distinctiveness"], distinctiveness_band)
        insufficiency_ok = _band_matches(case["should_insufficiency"], insufficiency_band)
        trust_ok = _band_matches(case["should_trust_adjustment"], trust_band)
        pass_count = int(commonness_ok) + int(distinctiveness_ok) + int(insufficiency_ok) + int(trust_ok)

        mismatches: List[str] = []
        if not commonness_ok:
            mismatches.append("commonness")
        if not distinctiveness_ok:
            mismatches.append("distinctiveness")
        if not insufficiency_ok:
            mismatches.append("insufficiency")
        if not trust_ok:
            mismatches.append("trust")

        rows.append(
            {
                "case": case["case"],
                "expected_match": case["expected_match"],
                "raw_device_similarity": raw_same_device,
                "commonness": breakdown.commonness_score,
                "distinctiveness": breakdown.distinctiveness_score,
                "collision_risk": breakdown.collision_risk,
                "insufficiency_risk": breakdown.insufficiency_risk,
                "trust_shift": breakdown.trust_shift,
                "trust_adjustment": breakdown.trust_adjustment,
                "final_profile_score": final_same_device,
                "confidence_label": breakdown.confidence_label,
                "policy_action": breakdown.policy_action,
                "uncertainty_zone": breakdown.uncertainty_zone,
                "obs_commonness_band": commonness_band,
                "obs_distinctiveness_band": distinctiveness_band,
                "obs_insufficiency_band": insufficiency_band,
                "obs_trust_band": trust_band,
                "should_commonness": case["should_commonness"],
                "should_distinctiveness": case["should_distinctiveness"],
                "should_insufficiency": case["should_insufficiency"],
                "should_trust_adjustment": case["should_trust_adjustment"],
                "semantic_check": "PASS" if pass_count == 4 else f"FAIL ({pass_count}/4)",
                "semantic_mismatches": ",".join(mismatches) if mismatches else "-",
                "policy_flags": ",".join(breakdown.policy_flags) if breakdown.policy_flags else "-",
            }
        )

    print(_format_table(rows))


def demo_single_scenarios():
    print("# Individual Scenario Types")
    
    # Show a few key scenarios
    scenarios_to_demo = [
        "BrowserDrift/Minor",
        "BrowserDrift/CrossBrowser",
        "PrivacyHardening/TorBrowser",
        "AdversarialPerturbation/CanvasNoise",
        "CommodityCollision/CorporateFleet",
    ]
    
    for scenario_type in scenarios_to_demo:
        test_rows: List[Dict[str, Any]] = []
        print(f"\n### {scenario_type}")
        pair = generate_scenario_pair(scenario_type)
        print('```') 
        print(f"Expected Match: {pair.metadata.expected_match}")
        print(f"Difficulty: {pair.metadata.difficulty}")
        print(f"Description: {pair.metadata.description}")
        print('```') 
        
        # Quick score
        breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=3)
        profile_scores = breakdown.profile_scores
        raw_profile_scores = breakdown.raw_profile_scores
        print(f"- Overall Confidence: {breakdown.overall_confidence:.1f}/100")
        print(f"- Raw Similarity: {breakdown.raw_similarity_score:.1f}/100")
        print(f"- Collision Risk: {breakdown.collision_risk:.1f}/100")
        print(f"- Insufficiency Risk: {breakdown.insufficiency_risk:.1f}/100")
        print(f"- Trust Shift: {breakdown.trust_shift:+.1f}")
        print(f"- Trust Adjustment: {breakdown.trust_adjustment:.1f}")
        print(f"- Confidence Label: {breakdown.confidence_label}")
        print(f"- Policy Action: {breakdown.policy_action}")
        print(f"- Uncertainty Zone: {breakdown.uncertainty_zone}")
        print(f"- Distinctiveness: {breakdown.distinctiveness_score:.1f}/100")
        print(f"- Commonness: {breakdown.commonness_score:.1f}/100")
        print(f"- Same Instance: {profile_scores.get('same_instance', breakdown.overall_confidence):.1f}/100")
        print(f"- Same Environment: {profile_scores.get('same_environment', breakdown.overall_confidence):.1f}/100")
        print(f"- Same Device: {profile_scores.get('same_device', breakdown.overall_confidence):.1f}/100")
        print(f"- Same Entity: {profile_scores.get('same_entity', breakdown.overall_confidence):.1f}/100")
        print(
             f"- Raw Same Device: "
             f"{raw_profile_scores.get('same_device', breakdown.raw_similarity_score):.1f}/100"
         )
        print(f"- Entropy Contribution: {breakdown.entropy_contribution:.1f}/100")
        print(f"- Attractor Risk: {breakdown.attractor_risk:.1f}/100")
        


def demo_scenario_categories():
    print("#  Scenario Categories")
    
    categories = get_scenario_categories()
    
    for category, scenario_types in categories.items():
        print(f"\n### {category}:")
        for st in scenario_types:
            print(f"  - {st}")


def demo_detailed_comparison():
    print("# Detailed Scenario Analysis")
    
    # Cross-browser scenario - should match but looks very different
    print("\n### Cross-Browser Scenario (Hard Case)")
    pair = generate_scenario_pair("BrowserDrift/CrossBrowser")
    
    print('```') 
    print(f"\nGround Truth: {pair.metadata.expected_match}")
    print(f"Difficulty: {pair.metadata.difficulty}")
    print(f"Description: {pair.metadata.description}\n")
    print('```') 
     
    breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=5)
    print('```') 
    print(format_breakdown(breakdown))
    print('```') 


def demo_attractor_collision():
    print("# Attractor Collision (Extreme Case)")
    
    # Corporate fleet - different users, identical setups
    print("\n###  Corporate Fleet Collision")
    pair = generate_scenario_pair("CommodityCollision/CorporateFleet")
    
    print('```')
    print(f"\nGround Truth: {pair.metadata.expected_match} (different users!)")
    print(f" Difficulty: {pair.metadata.difficulty}")
    print(f" Description: {pair.metadata.description}\n")
    
    breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=5)
    print(format_breakdown(breakdown))
    print('```')

    print("\n**False Positive Risk:**")
    print(f"- Attractor Risk: {breakdown.attractor_risk:.1f}/100")
    print(f"- Evidence Richness: {breakdown.evidence_richness:.1f}/100")
    print(f"- Structural Stability: {breakdown.structural_stability:.1f}/100")
    print("\b\b**High confidence, but they're different users!**")


def demo_privacy_hardening():
    print("# Privacy Hardening Scenarios")
    
    privacy_scenarios = [
        "PrivacyHardening/TorBrowser",
        "PrivacyHardening/ResistFingerprinting",
        "PrivacyHardening/CanvasDefender",
    ]
    
    for scenario_type in privacy_scenarios:
        print(f"\n### {scenario_type} ---")
        pair = generate_scenario_pair(scenario_type)
        print('```') 
        print(f"Expected Match: {pair.metadata.expected_match}")
        print(f"Description: {pair.metadata.description}")
        
        breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=2)
        
        print(f"\nScores:")
        print(f"  Overall Confidence: {breakdown.overall_confidence:.1f}/100")
        print(f"  Evidence Richness: {breakdown.evidence_richness:.1f}/100")
        print(f"  Entropy Contribution: {breakdown.entropy_contribution:.1f}/100")
        print(f"  Missing Fields: {len(breakdown.missing_fields)}")
        print('```') 
        
        if breakdown.evidence_richness < 60:
            print("\n**Low evidence - high-entropy fields missing or spoofed**")


def demo_dataset_generation():
    print("#  Balanced Dataset Generation")
    
    # Generate small balanced dataset
    dataset = generate_scenario_dataset(size=20)
    
    # Count by scenario type
    scenario_counts = {}
    expected_match_counts = {"True": 0, "False": 0}
    difficulty_counts = {}
    
    for pair in dataset:
        st = pair.metadata.scenario_type
        scenario_counts[st] = scenario_counts.get(st, 0) + 1
        
        match_key = str(pair.metadata.expected_match)
        expected_match_counts[match_key] += 1
        
        diff = pair.metadata.difficulty
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    print(f"\n\nGenerated {len(dataset)} scenario pairs\n\n")
    
    print("### By Scenario Type:")
    for st, count in sorted(scenario_counts.items()):
        print(f"-   {st}: {count}")
    
    print(f"\nBy Expected Match:")
    print(f"  Should Match: {expected_match_counts['True']}")
    print(f"  Should NOT Match: {expected_match_counts['False']}")
    
    print(f"\nBy Difficulty:")
    for diff, count in sorted(difficulty_counts.items()):
        print(f"  {diff}: {count}")


def demo_custom_distribution():
    print("## Custom Distribution (Focus on Hard Cases)")
    
    # Focus more on hard/extreme scenarios
    custom_distribution = {
        # Less focus on easy cases
        "BrowserDrift/Minor": 0.05,
        "EnvironmentChange/HomeOffice": 0.05,
        "MobilityChurn/TimezoneTravel": 0.05,
        
        # More focus on hard cases
        "BrowserDrift/CrossBrowser": 0.15,
        "PrivacyHardening/ResistFingerprinting": 0.10,
        "PrivacyHardening/CanvasDefender": 0.10,
        "AdversarialPerturbation/CanvasNoise": 0.10,
        "AdversarialPerturbation/FontRandomization": 0.05,
        
        # Heavy focus on extreme collision cases
        "PrivacyHardening/TorBrowser": 0.15,
        "CommodityCollision/CorporateFleet": 0.10,
        "CommodityCollision/iPhoneDefaults": 0.10,
    }
    
    dataset = generate_scenario_dataset(size=50, scenario_distribution=custom_distribution)
    
    print(f"\n  **Generated {len(dataset)} pairs with custom distribution**")
    print("\n\n** Focus: Hard and extreme cases (privacy, collisions, adversarial)**\n")
    
    # Analyze difficulty distribution
    difficulty_counts = {}
    for pair in dataset:
        diff = pair.metadata.difficulty
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    print("Difficulty Distribution:")
    for diff in ["easy", "medium", "hard", "extreme"]:
        count = difficulty_counts.get(diff, 0)
        pct = (count / len(dataset)) * 100
        print(f"  {diff}: {count} ({pct:.1f}%)")


def demo_profiled_scenario_benchmark():
    print("#  Scenario Benchmark (Profile-Aware)")

    dataset_size = 500
    dataset = generate_scenario_dataset(size=dataset_size)

    scored_pairs: List[Dict[str, Any]] = []
    for pair in dataset:
        breakdown = decompose_confidence(pair.fp1, pair.fp2, top_n=0)
        profile_scores = breakdown.profile_scores
        scored_pairs.append(
            {
                "scenario_type": pair.metadata.scenario_type,
                "difficulty": pair.metadata.difficulty,
                "sameDevice": pair.metadata.expected_match,
                "isAttractor": pair.metadata.difficulty == "extreme",
                "raw_overall": breakdown.raw_similarity_score,
                "overall": breakdown.overall_confidence,
                "trust_shift": breakdown.trust_shift,
                "trust_adjustment": breakdown.trust_adjustment,
                "collision_risk": breakdown.collision_risk,
                "insufficiency_risk": breakdown.insufficiency_risk,
                "uncertainty_zone": breakdown.uncertainty_zone,
                "confidence_label": breakdown.confidence_label,
                "policy_action": breakdown.policy_action,
                "distinctiveness": breakdown.distinctiveness_score,
                "commonness": breakdown.commonness_score,
                "same_instance": profile_scores.get("same_instance", breakdown.overall_confidence),
                "same_environment": profile_scores.get("same_environment", breakdown.overall_confidence),
                "same_device": profile_scores.get("same_device", breakdown.overall_confidence),
                "same_entity": profile_scores.get("same_entity", breakdown.overall_confidence),
                "richness": breakdown.evidence_richness,
                "attractor_risk": breakdown.attractor_risk,
            }
        )

    metrics_by_score = {
        "raw_overall": calculate_metrics(_as_metric_inputs(scored_pairs, "raw_overall")),
        "overall": calculate_metrics(_as_metric_inputs(scored_pairs, "overall")),
        "same_instance": calculate_metrics(_as_metric_inputs(scored_pairs, "same_instance")),
        "same_environment": calculate_metrics(_as_metric_inputs(scored_pairs, "same_environment")),
        "same_device": calculate_metrics(_as_metric_inputs(scored_pairs, "same_device")),
        "same_entity": calculate_metrics(_as_metric_inputs(scored_pairs, "same_entity")),
    }

    threshold_f1_rows: List[Dict[str, Any]] = []
    threshold_gap_rows: List[Dict[str, Any]] = []
    for index in range(len(metrics_by_score["overall"])):
        overall_row = metrics_by_score["overall"][index]
        instance_row = metrics_by_score["same_instance"][index]
        environment_row = metrics_by_score["same_environment"][index]
        device_row = metrics_by_score["same_device"][index]
        entity_row = metrics_by_score["same_entity"][index]

        threshold_f1_rows.append(
            {
                "threshold": overall_row.threshold,
                "raw_overall_f1": metrics_by_score["raw_overall"][index].f1,
                "overall_f1": overall_row.f1,
                "instance_f1": instance_row.f1,
                "environment_f1": environment_row.f1,
                "device_f1": device_row.f1,
                "entity_f1": entity_row.f1,
            }
        )
        threshold_gap_rows.append(
            {
                "threshold": overall_row.threshold,
                "raw_overall_gap": metrics_by_score["raw_overall"][index].far_frr_gap,
                "overall_gap": overall_row.far_frr_gap,
                "instance_gap": instance_row.far_frr_gap,
                "environment_gap": environment_row.far_frr_gap,
                "device_gap": device_row.far_frr_gap,
                "entity_gap": entity_row.far_frr_gap,
            }
        )

    scenario_rows: List[Dict[str, Any]] = []
    by_scenario: Dict[str, List[Dict[str, Any]]] = {}
    for row in scored_pairs:
        by_scenario.setdefault(str(row["scenario_type"]), []).append(row)

    for scenario_type in sorted(by_scenario.keys()):
        bucket = by_scenario[scenario_type]
        scenario_rows.append(
            {
                "scenario_type": scenario_type,
                "pairs": len(bucket),
                "expected_match_pct": _average([100.0 if b["sameDevice"] else 0.0 for b in bucket]),
                "raw_overall_mean": _average([float(b["raw_overall"]) for b in bucket]),
                "overall_mean": _average([float(b["overall"]) for b in bucket]),
                "trust_shift_mean": _average([float(b["trust_shift"]) for b in bucket]),
                "trust_adjustment_mean": _average([float(b["trust_adjustment"]) for b in bucket]),
                "collision_risk_mean": _average([float(b["collision_risk"]) for b in bucket]),
                "insufficiency_risk_mean": _average([float(b["insufficiency_risk"]) for b in bucket]),
                "uncertainty_zone_pct": _average(
                    [100.0 if bool(b["uncertainty_zone"]) else 0.0 for b in bucket]
                ),
                "low_confidence_pct": _average(
                    [100.0 if str(b["confidence_label"]) != "ordinary" else 0.0 for b in bucket]
                ),
                "distinctiveness_mean": _average([float(b["distinctiveness"]) for b in bucket]),
                "commonness_mean": _average([float(b["commonness"]) for b in bucket]),
                "instance_mean": _average([float(b["same_instance"]) for b in bucket]),
                "environment_mean": _average([float(b["same_environment"]) for b in bucket]),
                "device_mean": _average([float(b["same_device"]) for b in bucket]),
                "entity_mean": _average([float(b["same_entity"]) for b in bucket]),
                "richness_mean": _average([float(b["richness"]) for b in bucket]),
                "attractor_risk_mean": _average([float(b["attractor_risk"]) for b in bucket]),
            }
        )

    best_by_score = {
        name: max(rows, key=lambda item: item.f1)
        for name, rows in metrics_by_score.items()
    }
    true_eer_by_score = {
        name: calculate_true_eer(rows)
        for name, rows in metrics_by_score.items()
    }
    per_threshold_rows = [
        {
            "threshold": row.threshold,
            "precision": row.precision,
            "recall": row.recall,
            "f1": row.f1,
            "far": row.far,
            "frr": row.frr,
            "gap_far_frr": row.far_frr_gap,
        }
        for row in metrics_by_score["overall"]
    ]
    summary_rows = []
    for name in ["raw_overall", "overall", "same_instance", "same_environment", "same_device", "same_entity"]:
        best = best_by_score[name]
        eer = true_eer_by_score[name]
        summary_rows.append(
            {
                "profile": name,
                "best_f1_threshold": best.threshold,
                "best_f1": best.f1,
                "eer_threshold": eer.threshold,
                "eer": eer.eer,
            }
        )

    print(f"### Generated scenario pairs: {len(scored_pairs)}")
    print()
    print("### Scenario Type Means:")
    print(_format_table(scenario_rows))
    print("### Per-threshold table (overall):")
    print(_format_table(per_threshold_rows))
    print("### Benchmark summary:")
    print(_format_table(summary_rows))
    print("### Threshold Comparison (F1):")
    print(_format_table(threshold_f1_rows))
    print("### Threshold Comparison (FAR/FRR Gap):")
    print(_format_table(threshold_gap_rows))


def main():
    """Run all demos"""
    demo_single_scenarios()
    demo_scenario_categories()
    demo_detailed_comparison()
    demo_attractor_collision()
    demo_privacy_hardening()
    demo_dataset_generation()
    demo_custom_distribution()
    demo_profiled_scenario_benchmark()
    demo_trust_semantics_truth_table()
    
    print("\n\n# All scenarios Types:\n\n")
    for st in get_scenario_types():
        print(f"  - {st}")

    print("\n----\n")

if __name__ == "__main__":
    main()
