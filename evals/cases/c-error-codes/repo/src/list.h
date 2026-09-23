#ifndef LIST_H
#define LIST_H

#include <stddef.h>

typedef enum {
    LIST_OK = 0,
    LIST_ERR_ALLOC
} list_status_t;

typedef struct list list_t;

list_t *list_create(void);
void list_free(list_t *l);
list_status_t list_push(list_t *l, int value);
size_t list_size(const list_t *l);
int list_get(const list_t *l, size_t index);

#endif
