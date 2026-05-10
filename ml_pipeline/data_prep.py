import os
import shutil
from sklearn.model_selection import train_test_split

def organize_dataset(source_dir, dest_dir, test_size=0.2):
    """
    Splits a directory of class folders into train and validation sets.
    Example source_dir structure:
    source_dir/
      dry_road/
      low_waterlogging/
      high_waterlogging/
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    train_dir = os.path.join(dest_dir, 'train')
    val_dir = os.path.join(dest_dir, 'val')
    
    classes = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
    
    for cls in classes:
        cls_dir = os.path.join(source_dir, cls)
        images = [f for f in os.listdir(cls_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not images:
            continue
            
        train_imgs, val_imgs = train_test_split(images, test_size=test_size, random_state=42)
        
        # Create directories
        os.makedirs(os.path.join(train_dir, cls), exist_ok=True)
        os.makedirs(os.path.join(val_dir, cls), exist_ok=True)
        
        # Copy images
        for img in train_imgs:
            shutil.copy(os.path.join(cls_dir, img), os.path.join(train_dir, cls, img))
            
        for img in val_imgs:
            shutil.copy(os.path.join(cls_dir, img), os.path.join(val_dir, cls, img))
            
        print(f"Processed class '{cls}': {len(train_imgs)} train, {len(val_imgs)} validation")

if __name__ == "__main__":
    organize_dataset('./raw_dataset', './dataset')
    print("Data prep script ready.")
