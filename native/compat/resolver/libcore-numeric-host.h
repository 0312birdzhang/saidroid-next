/* Android10's netd numeric lookup uses inet_pton, including decimal leading
 * zero IPv4 octets. This glibc Portability adapter keeps real getaddrinfo and
 * freeaddrinfo ownership while rejecting inet_aton-only numeric syntax.
 * It also refuses Android network IDs/fwmarks the host cannot implement. */
#ifndef SAILDROID_LIBCORE_NUMERIC_HOST_H
#define SAILDROID_LIBCORE_NUMERIC_HOST_H
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <netdb.h>

static inline int sd_libcore_ipv4_decimal(const char *host, char normalized[16]) {
    unsigned octets[4];
    const unsigned char *at = reinterpret_cast<const unsigned char *>(host);
    for (unsigned index = 0; index != 4; ++index) {
        unsigned value = 0;
        if (*at < '0' || *at > '9') return 0;
        do {
            value = value * 10 + (*at++ - '0');
            if (value > 255) return 0;
        } while (*at >= '0' && *at <= '9');
        octets[index] = value;
        if (index != 3) {
            if (*at++ != '.') return 0;
        } else if (*at != '\0') return 0;
    }
    snprintf(normalized, 16, "%u.%u.%u.%u", octets[0], octets[1], octets[2], octets[3]);
    return 1;
}
static inline int sd_libcore_getaddrinfofornet(const char *host, const char *service,
        const struct addrinfo *hints, unsigned netid, unsigned mark, struct addrinfo **result) {
    if (!result) { errno = EINVAL; return EAI_SYSTEM; }
    *result = NULL;
    if (netid || mark) { errno = ENONET; return EAI_SYSTEM; }
    char normalized[16];
    if (host && hints && (hints->ai_flags & AI_NUMERICHOST) && !strchr(host, ':')) {
        if (!sd_libcore_ipv4_decimal(host, normalized)) return EAI_NONAME;
        host = normalized;
    }
    return getaddrinfo(host, service, hints, result);
}
#endif
