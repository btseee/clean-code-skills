#include "list.h"
#include <stdlib.h>

struct list {
    int *items;
    size_t size;
    size_t capacity;
};

list_t *list_create(void) {
    list_t *l = malloc(sizeof(*l));
    if (!l) return NULL;
    l->items = NULL;
    l->size = 0;
    l->capacity = 0;
    return l;
}

void list_free(list_t *l) {
    if (!l) return;
    free(l->items);
    free(l);
}

list_status_t list_push(list_t *l, int value) {
    if (l->size == l->capacity) {
        size_t new_capacity = l->capacity == 0 ? 4 : l->capacity * 2;
        int *items = realloc(l->items, new_capacity * sizeof(int));
        if (!items) return LIST_ERR_ALLOC;
        l->items = items;
        l->capacity = new_capacity;
    }
    l->items[l->size++] = value;
    return LIST_OK;
}

size_t list_size(const list_t *l) {
    return l->size;
}

int list_get(const list_t *l, size_t index) {
    return l->items[index];
}
