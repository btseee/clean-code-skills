#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface FeedItem : NSObject <NSSecureCoding>

@property (nonatomic, copy, readonly) NSString *identifier;
@property (nonatomic, copy, readonly) NSString *title;

- (instancetype)initWithIdentifier:(NSString *)identifier title:(NSString *)title;

@end

NS_ASSUME_NONNULL_END
