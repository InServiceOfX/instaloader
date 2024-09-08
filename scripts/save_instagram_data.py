from public_instagram_loader import InstagramData, load_config
import json
from pathlib import Path

def save_instagram_data(instagram_data: InstagramData, base_path: Path = None):
    if base_path is None:
        config = load_config()
        base_path = Path(config['public_profile'].get('save_directory', '.'))
    
    profile_dir = base_path / instagram_data.profile_info['username']
    profile_dir.mkdir(parents=True, exist_ok=True)

    # Save profile info
    with open(profile_dir / 'profile_info.json', 'w') as f:
        json.dump(instagram_data.profile_info, f, indent=2)

    # Save posts
    posts_dir = profile_dir / 'posts'
    posts_dir.mkdir(exist_ok=True)
    for post in instagram_data.posts:
        post_dir = posts_dir / post['shortcode']
        post_dir.mkdir(exist_ok=True)
        
        # Move image file
        old_path = Path(post['filename'])
        new_path = post_dir / old_path.name
        if old_path.exists():
            old_path.rename(new_path)
        
        # Save post data
        with open(post_dir / 'post_data.json', 'w') as f:
            json.dump(post, f, indent=2)
        
        # Save caption
        if post['caption']:
            with open(post_dir / 'caption.txt', 'w', encoding='utf-8') as f:
                f.write(post['caption'])

    # Save highlights
    highlights_dir = profile_dir / 'highlights'
    highlights_dir.mkdir(exist_ok=True)
    for highlight in instagram_data.highlights:
        highlight_dir = highlights_dir / highlight['highlight_title']
        highlight_dir.mkdir(exist_ok=True)
        
        # Move image file
        old_path = Path(highlight['filename'])
        new_path = highlight_dir / old_path.name
        if old_path.exists():
            old_path.rename(new_path)
        
        # Save highlight data
        with open(highlight_dir / 'highlight_data.json', 'w') as f:
            json.dump(highlight, f, indent=2)
        
        # Save caption
        if highlight['caption']:
            with open(highlight_dir / 'caption.txt', 'w', encoding='utf-8') as f:
                f.write(highlight['caption'])

    print(f"Data saved for {instagram_data.profile_info['username']} in {profile_dir}")

if __name__ == "__main__":
    import sys
    from public_instagram_loader import public_instagram_loader

    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    data = public_instagram_loader(config_path)
    save_instagram_data(data)
    print(f"Collected and saved data for {data.profile_info['username']}:")
    print(f"Total posts: {len(data.posts)}")
    print(f"Total highlights: {len(data.highlights)}")