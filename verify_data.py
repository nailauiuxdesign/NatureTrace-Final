from utils.data_utils import get_snowflake_connection
import pandas as pd

def verify_initial_data():
    """Verify that the initial data was successfully loaded"""
    print("Verifying Initial Data in NatureTrace Database")
    print("=" * 50)
    
    try:
        conn = get_snowflake_connection()
        if not conn:
            print("❌ Cannot connect to database")
            return
        
        # Get total count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total records in database: {total_count}")
        
        # Get count by category
        cursor.execute("SELECT category, COUNT(*) FROM animal_insight_data WHERE category IS NOT NULL GROUP BY category ORDER BY COUNT(*) DESC")
        categories = cursor.fetchall()
        
        if categories:
            print("\n📋 Records by Category:")
            for category, count in categories:
                print(f"   - {category}: {count} records")
        
        # Get sample data with new fields
        cursor.execute("""
            SELECT name, category, wikipedia_url, 
                   CASE WHEN inatural_pic IS NOT NULL AND inatural_pic != '' THEN 'Yes' ELSE 'No' END as has_inatural_pic,
                   CASE WHEN original_image IS NOT NULL AND original_image != '' THEN 'Yes' ELSE 'No' END as has_wikipedia_image,
                   CASE WHEN summary IS NOT NULL AND summary != '' THEN 'Yes' ELSE 'No' END as has_summary
            FROM animal_insight_data 
            WHERE category IS NOT NULL 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        sample_data = cursor.fetchall()
        
        if sample_data:
            print("\n🔬 Sample Data (Latest 10 records):")
            print("-" * 100)
            print(f"{'Name':<20} {'Category':<15} {'iNat Pic':<10} {'Wiki Img':<10} {'Summary':<10} {'Wikipedia URL':<30}")
            print("-" * 100)
            
            for row in sample_data:
                name, category, wiki_url, has_inat, has_wiki_img, has_summary = row
                wiki_short = (wiki_url[:27] + "...") if wiki_url and len(wiki_url) > 30 else (wiki_url or "None")
                print(f"{name[:19]:<20} {category[:14]:<15} {has_inat:<10} {has_wiki_img:<10} {has_summary:<10} {wiki_short:<30}")
        
        # Check data completeness
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(category) as has_category,
                COUNT(inatural_pic) as has_inatural_pic,
                COUNT(wikipedia_url) as has_wikipedia_url,
                COUNT(original_image) as has_original_image,
                COUNT(species) as has_species,
                COUNT(summary) as has_summary
            FROM animal_insight_data
        """)
        
        completeness = cursor.fetchone()
        
        if completeness:
            total, cat, inat, wiki_url, orig_img, species, summary = completeness
            print(f"\n📈 Data Completeness:")
            print(f"   - Category: {cat}/{total} ({(cat/total*100):.1f}%)")
            print(f"   - iNaturalist Images: {inat}/{total} ({(inat/total*100):.1f}%)")
            print(f"   - Wikipedia URLs: {wiki_url}/{total} ({(wiki_url/total*100):.1f}%)")
            print(f"   - Wikipedia Images: {orig_img}/{total} ({(orig_img/total*100):.1f}%)")
            print(f"   - Species Info: {species}/{total} ({(species/total*100):.1f}%)")
            print(f"   - Summaries: {summary}/{total} ({(summary/total*100):.1f}%)")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Data verification complete!")
        
        if total_count > 0:
            print(f"🎉 Success! Your NatureTrace database now contains {total_count} records with iNaturalist and Wikipedia data!")
        else:
            print("⚠️  No data found. Please run fetch_initial_data.py to populate the database.")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    verify_initial_data()
