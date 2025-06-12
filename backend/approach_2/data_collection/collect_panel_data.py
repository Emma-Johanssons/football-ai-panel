import os
import json
from data_collection.youtube_collector import YouTubeCollector

def main():
    # Create collector
    collector = YouTubeCollector()
    
    # Collect data from all shows (5 videos per show)
    print("Starting data collection from football panel shows...")
    results = collector.collect_all_shows(max_videos_per_show=5)
    
    # Save overall results
    output_file = os.path.join(os.getenv("LEARNING_DATA_DIR", "/app/learning_data"), "panelist_statistics.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Data collection complete. Results saved to {output_file}")
    
    # Print some statistics
    print("\nPanelist Statistics:")
    stats = collector.get_panelist_statistics()
    for panelist, analysis in stats.items():
        print(f"\n{panelist}:")
        print("Personality Traits:")
        for trait, value in analysis["personality_traits"].items():
            print(f"  {trait}: {value:.2f}")
        print("Conversation Patterns:")
        for pattern, value in analysis["conversation_patterns"].items():
            print(f"  {pattern}: {value:.2f}")

if __name__ == "__main__":
    main() 