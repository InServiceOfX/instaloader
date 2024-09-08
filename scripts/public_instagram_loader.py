import yaml
from instaloader import Instaloader, Profile, StoryItem
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict
import json
import shutil
from instaloader.exceptions import LoginRequiredException
import signal
from contextlib import contextmanager

@dataclass
class InstagramData:
    profile_info: Dict
    posts: List[Dict] = field(default_factory=list)
    highlights: List[Dict] = field(default_factory=list)

class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def load_config(config_path: Path = None):
    if config_path is None:
        repo_root = Path(__file__).resolve().parent.parent
        config_path = repo_root / 'Configurations' / 'public_profile.yml'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with config_path.open('r') as file:
        return yaml.safe_load(file)

def public_instagram_loader(config_path: Path = None):
    config = load_config(config_path)
    username = config['username']
    save_directory = Path(config.get('save_directory', '.'))

    # Create profile-specific subdirectory
    profile_dir = save_directory / username
    profile_dir.mkdir(parents=True, exist_ok=True)

    L = Instaloader(
        download_pictures=True,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        dirname_pattern=str(profile_dir)
    )

    profile = Profile.from_username(L.context, username)

    profile_info = {
        'username': profile.username,
        'full_name': profile.full_name,
        'biography': profile.biography,
        'followers': profile.followers,
        'followees': profile.followees,
        'mediacount': profile.mediacount,
    }

    instagram_data = InstagramData(profile_info=profile_info)

    print(f"Downloading posts from {username}")
    for post in profile.get_posts():
        if post.typename == 'GraphImage':
            post_data = {
                'shortcode': post.shortcode,
                'caption': post.caption,
                'date': post.date_local,
                'likes': post.likes,
                'filename': f"{post.date_utc:%Y-%m-%d_%H-%M-%S}_UTC",
            }
            L.download_pic(filename=post_data['filename'], url=post.url, mtime=post.date_utc)
            instagram_data.posts.append(post_data)

    # TODO: not working.
    """
    print(f"Downloading highlights from {username}")
    try:
        for highlight in L.get_highlights(profile):
            for item in highlight.get_items():
                if isinstance(item, StoryItem) and item.typename == 'GraphImage':
                    highlight_data = {
                        'highlight_title': highlight.title,
                        'caption': item.caption,
                        'date': item.date_local,
                        'filename': f"highlight_{item.date_utc:%Y-%m-%d_%H-%M-%S}_UTC",
                    }
                    L.download_pic(filename=highlight_data['filename'], url=item.url, mtime=item.date_utc)
                    instagram_data.highlights.append(highlight_data)
    except LoginRequiredException:
        print("Login required for highlights. Skipping highlights download.")
    """
        
    return instagram_data

def cleanup_and_save(instagram_data: InstagramData, profile_dir: Path):
    # Move any stray .jpg files
    for jpg_file in Path('.').glob('*.jpg'):
        shutil.move(str(jpg_file), str(profile_dir / jpg_file.name))
    
    # Save InstagramData
    with open(profile_dir / 'instagram_data.json', 'w') as f:
        json.dump(instagram_data.__dict__, f, indent=2, default=str)

    print(f"Cleanup completed. Data saved in {profile_dir}")

if __name__ == "__main__":
    import sys

    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    config = load_config(config_path)
    save_directory = Path(config.get('save_directory', '.'))
    profile_dir = save_directory / config['username']
    timeout_seconds = config.get('timeout', 300)  # Default timeout of 5 minutes

    data = InstagramData(profile_info={'username': config['username']})
    try:
        with time_limit(timeout_seconds):
            data = public_instagram_loader(config_path)
    except TimeoutException:
        print(f"Operation timed out after {timeout_seconds} seconds. Saving partial data.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        cleanup_and_save(data, profile_dir)

    print(f"Collected and saved data for {data.profile_info['username']}:")
    print(f"Total posts: {len(data.posts)}")
    print(f"Total highlights: {len(data.highlights)}")