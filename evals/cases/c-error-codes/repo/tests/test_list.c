#include "list.h"
#include <assert.h>

int main(void) {
    list_t *l = list_create();
    assert(list_push(l, 1) == LIST_OK);
    assert(list_push(l, 2) == LIST_OK);
    assert(list_size(l) == 2);
    assert(list_get(l, 0) == 1);
    list_free(l);
    return 0;
}
