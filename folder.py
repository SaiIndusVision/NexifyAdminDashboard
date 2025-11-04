# from google.cloud import storage
# from datetime import datetime
# import json
# from google.oauth2 import service_account
# from multiprocessing import Pool, cpu_count, Manager
# import time
# from functools import partial

# # GCP setup
# credentials_info = {
#   "type": "service_account",
#   "project_id": "sunlit-setup-439407-a5",
#   "private_key_id": "474a14c230a7fddbb34d621870ef553761543799",
#   "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCu8aur7SAgy0Wl\nbFpHRHGVOoTOElxIUe9XDaLhs3qx70rXOz9SWSFcOyAM1eh2YGdc2HwylSvV+lrY\nHg+xV5KVomudfmNS0EngBQp8pRcvYqw2frJLUuG6zylg75kV1TPJFmZo84RZ2vDy\nGU3c/tAKWFOp3Cy+Q42LYiTuZIZu59z5SuF6kFFx2CpBUP7llfLS3a5u1o1yqea8\nDA75l0Za1xi5zQ3ojkNPn9lRNd0A9rXb61GkgxgaBZIMEAOgp56AJ3jqwo91AmQU\nqXdNwEb1UaZHuh/h/6vReHnLs+zGJoG8Sg+EqrXebGqAtAzwnetC5lrbzFBM9ztI\nsmSs0tqXAgMBAAECggEALSNa3YXVw9Be3HNMCdZdjhjmujrfh6NoYyg4Dg8eibmJ\nsGXvjSJFKsRwnQ82JxDxqnGK/gwiHtg1R0zeVK4ZOrWJGb5KB0yJuxzh205HYKkP\ncRIYk7nDV01rSkEX2RvE/E3kx5CJZhvJDlY8EljGudyXXZzbCI5qf3untsDGNOf9\nJmOcsdYF/CCDwK1QwRh7ZplactGYVYjD/DdFpQ9ExYiO5MIfP+nzmjyDwIzFM1nR\nAYIXbzUqXfp+/XYXvscjHV6rkd9sDWxvBIq5EMH/DIA7zFY8Kp6YR65TKRiuGz7e\nA2xO2HLy40USK3Octu7n+I/mjL7V1pPfEdscre3erQKBgQDxK5p4gBd1cRMHiqPb\ndpNAN4PXwPRoyCkkETPC+Z/P3mj/aiZYIpZqmyVhjSYwTYp2CH7cORMG7Id8TBsn\nupN8Gwq0cm1W5hrgVnkrNyhUIXQkh3Et0DBmTeTBpMSBVyIICrGxebFI3Ek/rsG7\n8AdgNp0IMU7cbauezxz7CTId+wKBgQC5s4/jq0ZGEzeqyKVR58oLyMutwTkrfAAw\nSNvTk2736IsRuqQosENDZa76pSlNRnjFk+WuTTAMhxjkwHJ/dZwUlIRj31GkP0s/\nFgYf7zcJVwdmkTVa6YjrkQbdVfAe3f9U5JpDZrMZHhXaYk/QoH0gIkdDI2cbByOe\nQ/jiuy8fFQKBgH/YAnHATS83esPzrXroN5TCGQTlR2rIOG7jI5JG632ww+4pohv0\ncdIfXkiBH25ZnH2HcWBibQCtoAC3A2ojEI2odBtF0UpQfozPqjnLanh2p2+50Lhd\ndVq2Df7MzlJWEzc6HAodnWonRDka9Z4f1nkdWk7+fHSDOofb+NvmewfDAoGAf6L4\nkl5llcKdr2froUk0qTbhL9MwLUA0jPt3BIxAaGrQM2ZacJD+GnPoeeRNaAy48+w8\noLny/ZlZtdjEmfDHT6no+RBEeCT83iaQHSD5bhUARDIoPw1nC6qJ0lXADic92Sar\nFQqgrPHtyUVrYJT+i7ijzHSn6H7Wr3A+v/AyaiUCgYBdtdR0qtIy5pK0HycBQ7tV\nTXWqs5vHExfLQ7Wf83mZFUX2pjKeznc/dLf4OlU87+euXbVdPHfccqioyfji0Up0\nO152LrkO/PQs5cK4+jqqNOg9PuOZX9foxjMCR1gneWnP+zlAtRIsELfvTZy+zS2L\ncitiIMTELNDJe+ApfCuoJA==\n-----END PRIVATE KEY-----\n",
#   "client_email": "vinstorage@sunlit-setup-439407-a5.iam.gserviceaccount.com",
#   "client_id": "109362186121124951427",
#   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#   "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/vinstorage%40sunlit-setup-439407-a5.iam.gserviceaccount.com",
#   "universe_domain": "googleapis.com"
# }

# KEEP_LIMIT = 20000
# BUCKET_NAME = "vin-dashboard"
# BASE_DIRS = ["2"]
# NUM_PROCESSES = min(cpu_count() * 2, 16)  # Use 2x CPU cores, max 16 processes

# def delete_blob_batch(args):
#     """Delete a batch of blobs - designed to run in parallel"""
#     blob_names, bucket_name, credentials_info, process_id, progress_dict = args
    
#     # Create client for this process
#     credentials = service_account.Credentials.from_service_account_info(credentials_info)
#     client = storage.Client(credentials=credentials, project=credentials_info["project_id"])
#     bucket = client.bucket(bucket_name)
    
#     deleted_count = 0
#     failed_count = 0
#     total_size_deleted = 0
    
#     for i, blob_name in enumerate(blob_names):
#         try:
#             blob = bucket.blob(blob_name)
#             # Get size before deletion (if available)
#             try:
#                 file_size = blob.size or 0
#             except:
#                 file_size = 0
            
#             blob.delete()
#             deleted_count += 1
#             total_size_deleted += file_size
            
#         except Exception as e:
#             failed_count += 1
#             print(f"  ⚠️ Process {process_id}: Failed to delete {blob_name}: {str(e)[:100]}")
    
#     # Update shared progress
#     with progress_dict.get_lock():
#         progress_dict['deleted'] += deleted_count
#         progress_dict['failed'] += failed_count
#         progress_dict['size_deleted'] += total_size_deleted
#         progress_dict['processed_batches'] += 1
    
#     return {
#         'process_id': process_id,
#         'deleted': deleted_count,
#         'failed': failed_count,
#         'size_deleted': total_size_deleted
#     }

# def split_into_batches(items, batch_size):
#     """Split a list into batches of specified size"""
#     for i in range(0, len(items), batch_size):
#         yield items[i:i + batch_size]

# def main():
#     credentials = service_account.Credentials.from_service_account_info(credentials_info)
#     client = storage.Client(credentials=credentials, project=credentials_info["project_id"])
#     bucket = client.bucket(BUCKET_NAME)

#     print(f"🚀 Using {NUM_PROCESSES} parallel processes for deletion")
    
#     for base_folder in BASE_DIRS:
#         print(f"\n📁 Processing folder: {base_folder}/")
#         print("=" * 50)

#         # List all blobs in the folder (excluding directories)
#         print("🔍 Fetching file list...")
#         start_time = time.time()
#         blobs = list(bucket.list_blobs(prefix=f"{base_folder}/"))
#         blobs = [blob for blob in blobs if not blob.name.endswith('/')]
#         list_time = time.time() - start_time

#         total_files = len(blobs)
#         print(f"📊 Total files found: {total_files:,} (took {list_time:.1f}s)")

#         if total_files <= KEEP_LIMIT:
#             print(f"✅ Folder has {total_files:,} files, which is within the {KEEP_LIMIT:,} limit. No deletion needed.")
#             continue

#         # Sort by updated time (newest first)
#         print("🔄 Sorting files by update time (newest first)...")
#         sort_start = time.time()
#         blobs.sort(key=lambda b: b.updated, reverse=True)
#         sort_time = time.time() - sort_start
#         print(f"   Sorting took {sort_time:.1f}s")
        
#         # Show overall date range of all files
#         if blobs:
#             oldest_overall = min(blobs, key=lambda b: b.updated)
#             newest_overall = max(blobs, key=lambda b: b.updated)
#             print(f"📅 All files date range: {oldest_overall.updated.strftime('%Y-%m-%d %H:%M')} to {newest_overall.updated.strftime('%Y-%m-%d %H:%M')}")
        
#         # Files to keep (newest KEEP_LIMIT files)
#         files_to_keep = blobs[:KEEP_LIMIT]
#         files_to_delete = blobs[KEEP_LIMIT:]

#         print(f"✅ Files to keep: {len(files_to_keep):,} (newest {KEEP_LIMIT:,})")
#         print(f"🗑️ Files to delete: {len(files_to_delete):,}")
        
#         if len(files_to_delete) == 0:
#             print("✅ No files to delete!")
#             continue

#         # Show date range of files being kept vs deleted
#         if files_to_keep:
#             newest_kept = files_to_keep[0].updated
#             oldest_kept = files_to_keep[-1].updated
#             print(f"📅 Keeping files from {oldest_kept.strftime('%Y-%m-%d %H:%M')} to {newest_kept.strftime('%Y-%m-%d %H:%M')}")
        
#         if files_to_delete:
#             newest_deleted = files_to_delete[0].updated
#             oldest_deleted = files_to_delete[-1].updated
#             print(f"🗑️ Deleting files from {oldest_deleted.strftime('%Y-%m-%d %H:%M')} to {newest_deleted.strftime('%Y-%m-%d %H:%M')}")

#         # Ask for confirmation if deleting many files
#         if len(files_to_delete) > 1000:
#             response = input(f"\n⚠️ About to delete {len(files_to_delete):,} files using {NUM_PROCESSES} parallel processes. Continue? (y/N): ")
#             if response.lower() != 'y':
#                 print("❌ Skipping deletion for this folder.")
#                 continue

#         # Prepare for parallel deletion
#         print(f"\n🗑️ Starting parallel deletion of {len(files_to_delete):,} files...")
        
#         # Split files into batches for each process
#         batch_size = max(1, len(files_to_delete) // (NUM_PROCESSES * 4))  # 4 batches per process
#         batches = list(split_into_batches([blob.name for blob in files_to_delete], batch_size))
        
#         print(f"   Split into {len(batches)} batches of ~{batch_size} files each")
        
#         # Shared progress tracking
#         with Manager() as manager:
#             progress_dict = manager.dict({
#                 'deleted': 0,
#                 'failed': 0,
#                 'size_deleted': 0,
#                 'processed_batches': 0
#             })
            
#             # Prepare arguments for each batch
#             batch_args = []
#             for i, batch in enumerate(batches):
#                 batch_args.append((
#                     batch,
#                     BUCKET_NAME,
#                     credentials_info,
#                     i + 1,
#                     progress_dict
#                 ))
            
#             deletion_start = time.time()
            
#             # Start parallel deletion with progress monitoring
#             with Pool(processes=NUM_PROCESSES) as pool:
#                 # Start async deletion
#                 result = pool.map_async(delete_blob_batch, batch_args)
                
#                 # Monitor progress
#                 total_batches = len(batches)
#                 while not result.ready():
#                     time.sleep(2)  # Check every 2 seconds
#                     current_deleted = progress_dict.get('deleted', 0)
#                     current_failed = progress_dict.get('failed', 0)
#                     processed_batches = progress_dict.get('processed_batches', 0)
                    
#                     if processed_batches > 0:
#                         progress_pct = (processed_batches / total_batches) * 100
#                         print(f"  🔄 Progress: {processed_batches}/{total_batches} batches ({progress_pct:.1f}%) - "
#                               f"Deleted: {current_deleted:,}, Failed: {current_failed}")
                
#                 # Get final results
#                 batch_results = result.get()
            
#             deletion_time = time.time() - deletion_start
            
#             # Final summary
#             total_deleted = progress_dict['deleted']
#             total_failed = progress_dict['failed']
#             total_size_deleted = progress_dict['size_deleted']
            
#             print(f"\n📈 Summary for folder '{base_folder}':")
#             print(f"  ✅ Successfully deleted: {total_deleted:,} files")
#             print(f"  ❌ Failed deletions: {total_failed}")
#             print(f"  💾 Total space freed: {total_size_deleted / (1024*1024):.2f} MB")
#             print(f"  📁 Remaining files: {total_files - total_deleted:,}")
#             print(f"  ⏱️ Deletion time: {deletion_time:.1f}s")
#             print(f"  🚀 Average speed: {total_deleted/deletion_time:.1f} files/second")

# def dry_run():
#     """Run without actually deleting files to see what would be deleted"""
#     credentials = service_account.Credentials.from_service_account_info(credentials_info)
#     client = storage.Client(credentials=credentials, project=credentials_info["project_id"])
#     bucket = client.bucket(BUCKET_NAME)

#     print("🔍 DRY RUN - No files will be deleted")
#     print("=" * 50)

#     total_files_to_delete = 0
#     total_space_to_free = 0

#     for base_folder in BASE_DIRS:
#         print(f"\n📁 Analyzing folder: {base_folder}/")
        
#         start_time = time.time()
#         blobs = list(bucket.list_blobs(prefix=f"{base_folder}/"))
#         blobs = [blob for blob in blobs if not blob.name.endswith('/')]
#         list_time = time.time() - start_time
        
#         total_files = len(blobs)
#         print(f"📊 Total files: {total_files:,} (fetched in {list_time:.1f}s)")
        
#         if total_files <= KEEP_LIMIT:
#             print(f"✅ Within limit ({KEEP_LIMIT:,}). No deletion needed.")
#             continue
            
#         blobs.sort(key=lambda b: b.updated, reverse=True)
        
#         # Show overall date range of all files
#         if blobs:
#             oldest_overall = min(blobs, key=lambda b: b.updated)
#             newest_overall = max(blobs, key=lambda b: b.updated)
#             print(f"📅 All files date range: {oldest_overall.updated.strftime('%Y-%m-%d %H:%M')} to {newest_overall.updated.strftime('%Y-%m-%d %H:%M')}")
        
#         files_to_keep = blobs[:KEEP_LIMIT]
#         files_to_delete = blobs[KEEP_LIMIT:]
        
#         # Show what would be kept vs deleted
#         if files_to_keep:
#             newest_kept = files_to_keep[0].updated
#             oldest_kept = files_to_keep[-1].updated
#             print(f"📅 Would keep files from: {oldest_kept.strftime('%Y-%m-%d %H:%M')} to {newest_kept.strftime('%Y-%m-%d %H:%M')}")
        
#         total_size_to_delete = sum(blob.size or 0 for blob in files_to_delete)
        
#         print(f"🗑️ Would delete: {len(files_to_delete):,} files")
#         print(f"💾 Space to be freed: {total_size_to_delete / (1024*1024):.2f} MB")
        
#         total_files_to_delete += len(files_to_delete)
#         total_space_to_free += total_size_to_delete
        
#         if files_to_delete:
#             oldest_to_delete = min(files_to_delete, key=lambda b: b.updated)
#             newest_to_delete = max(files_to_delete, key=lambda b: b.updated)
#             print(f"📅 Would delete files from: {oldest_to_delete.updated.strftime('%Y-%m-%d %H:%M')} to {newest_to_delete.updated.strftime('%Y-%m-%d %H:%M')}")

#         # Show some sample files that would be deleted (first 5 and last 5)
#         if files_to_delete and len(files_to_delete) > 10:
#             print(f"📋 Sample files to delete (showing first 5 and last 5):")
#             print("   First 5 (newest to be deleted):")
#             for i, blob in enumerate(files_to_delete[:5]):
#                 print(f"     {i+1}. {blob.name} - {blob.updated.strftime('%Y-%m-%d %H:%M:%S')}")
#             print("   Last 5 (oldest to be deleted):")
#             for i, blob in enumerate(files_to_delete[-5:]):
#                 print(f"     {i+1}. {blob.name} - {blob.updated.strftime('%Y-%m-%d %H:%M:%S')}")

#     print(f"\n🎯 TOTAL SUMMARY:")
#     print(f"📊 Total files to delete: {total_files_to_delete:,}")
#     print(f"💾 Total space to free: {total_space_to_free / (1024*1024):.2f} MB")
#     if total_files_to_delete > 0:
#         estimated_time = total_files_to_delete / (NUM_PROCESSES * 10)  # Rough estimate: 10 files/sec per process
#         print(f"⏱️ Estimated deletion time: {estimated_time:.1f} seconds with {NUM_PROCESSES} processes")

# if __name__ == "__main__":
#     print(f"🖥️ System has {cpu_count()} CPU cores, using {NUM_PROCESSES} processes")
    
#     # Run a dry run first to see what would be deleted
#     dry_run()
    
#     print(f"\n{'='*60}")
#     print("To run the actual deletion, uncomment the main() call below")
#     print("="*60)
    
#     # Uncomment the next line to run the actual deletion after reviewing dry run results
#     # main()