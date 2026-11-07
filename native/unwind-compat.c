/* libunwind 1.8 exports this new API in the architecture library without the
 * LOCAL_ONLY prefix. Preserve its actual prototype when providing that alias.
 * This is a private build/test dependency, not a replacement system library.
 */
#define _GNU_SOURCE
#include <libunwind.h>

void _ULaarch64_set_iterate_phdr_function(unw_addr_space_t address_space,
                                         unw_iterate_phdr_func_t iterator) {
    unw_set_iterate_phdr_function(address_space, iterator);
}
