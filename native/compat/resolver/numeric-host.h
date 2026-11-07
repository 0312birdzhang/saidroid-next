/* Android 10 netd explore_numeric uses inet_pton, while glibc getaddrinfo
 * accepts inet_aton shorthand, octal and hexadecimal IPv4. Keep the existing
 * translator's address ownership and ABI conversion; normalize only the
 * IPv4 numeric-host input. Android's leading zero octets are decimal.
 * IPv6 (including scopes), DNS, services, and network selection retain the
 * existing resolver path. See source provenance next to this header. */
#ifndef SAILDROID_NUMERIC_HOST_H
#define SAILDROID_NUMERIC_HOST_H

static int sd_numeric_ipv4_decimal(const char *host, char normalized[16]) {
    unsigned octets[4];
    const unsigned char *at = (const unsigned char *)host;
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

struct bionic_addrinfo;
int bionic_android_getaddrinfofornet(const char *host, const char *service,
        const struct bionic_addrinfo *hints, unsigned netid, unsigned mark,
        struct bionic_addrinfo **result) {
    if (!result) { errno = EINVAL; return EAI_SYSTEM; }
    *result = NULL;
    if (netid || mark) { errno = ENONET; return EAI_SYSTEM; }
    int flags = 0;
    /* ai_flags is the first int in both existing translator and Android ABI. */
    if (hints) memcpy(&flags, hints, sizeof(flags));
    char normalized[16];
    if (host && (flags & AI_NUMERICHOST) && !strchr(host, ':')) {
        if (!sd_numeric_ipv4_decimal(host, normalized)) return EAI_NONAME;
        host = normalized;
    }
    int (*resolve)(const char *, const char *, const struct bionic_addrinfo *,
                   struct bionic_addrinfo **) = dlsym(RTLD_DEFAULT, "bionic_getaddrinfo");
    if (!resolve) { errno = ENOSYS; return EAI_SYSTEM; }
    return resolve(host, service, hints, result);
}
#endif
