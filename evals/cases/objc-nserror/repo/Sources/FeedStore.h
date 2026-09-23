#import <Foundation/Foundation.h>
#import "FeedItem.h"

NS_ASSUME_NONNULL_BEGIN

@interface FeedStore : NSObject

- (BOOL)saveFeedItems:(NSArray<FeedItem *> *)items;

@end

NS_ASSUME_NONNULL_END
