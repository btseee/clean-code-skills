#import "FeedItem.h"

@implementation FeedItem

- (instancetype)initWithIdentifier:(NSString *)identifier title:(NSString *)title {
    self = [super init];
    if (self) {
        _identifier = [identifier copy];
        _title = [title copy];
    }
    return self;
}

+ (BOOL)supportsSecureCoding {
    return YES;
}

- (instancetype)initWithCoder:(NSCoder *)coder {
    NSString *identifier = [coder decodeObjectOfClass:[NSString class] forKey:@"identifier"];
    NSString *title = [coder decodeObjectOfClass:[NSString class] forKey:@"title"];
    return [self initWithIdentifier:identifier title:title];
}

- (void)encodeWithCoder:(NSCoder *)coder {
    [coder encodeObject:self.identifier forKey:@"identifier"];
    [coder encodeObject:self.title forKey:@"title"];
}

@end
