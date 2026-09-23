#import "FeedStore.h"

@implementation FeedStore

- (BOOL)saveFeedItems:(NSArray<FeedItem *> *)items {
    NSData *data = [NSKeyedArchiver archivedDataWithRootObject:items
                                          requiringSecureCoding:YES
                                                          error:nil];
    if (!data) {
        NSLog(@"failed to archive feed items");
        return NO;
    }

    NSURL *fileURL = [self storageURL];
    BOOL success = [data writeToURL:fileURL atomically:YES];
    if (!success) {
        NSLog(@"failed to write feed items to disk");
    }
    return success;
}

- (NSURL *)storageURL {
    NSArray<NSURL *> *urls = [[NSFileManager defaultManager] URLsForDirectory:NSCachesDirectory
                                                                     inDomains:NSUserDomainMask];
    return [urls.firstObject URLByAppendingPathComponent:@"feed.data"];
}

@end
