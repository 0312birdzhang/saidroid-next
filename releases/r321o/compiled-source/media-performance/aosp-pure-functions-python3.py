def perc(data, p, fn=round):
  """Returns a percentile value from a sorted array.

  Arguments:
    data: sorted data
    p:    percentile value (0-100)
    fn:   method used for rounding the percentile to an integer index in data
  """
  return data[int(fn((len(data) - 1) * p / 100))]


def genXml(data, A=None):
  yield '<?xml version="1.0" encoding="utf-8" ?>'
  yield '<!-- Copyright 2016 The Android Open Source Project'
  yield ''
  yield '     Licensed under the Apache License, Version 2.0 (the "License");'
  yield '     you may not use this file except in compliance with the License.'
  yield '     You may obtain a copy of the License at'
  yield ''
  yield '          http://www.apache.org/licenses/LICENSE-2.0'
  yield ''
  yield '     Unless required by applicable law or agreed to in writing, software'
  yield '     distributed under the License is distributed on an "AS IS" BASIS,'
  yield '     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.'
  yield '     See the License for the specific language governing permissions and'
  yield '     limitations under the License.'
  yield '-->'
  yield ''
  yield '<MediaCodecs>'
  last_section = None
  from collections import namedtuple
  Comp = namedtuple('Comp', 'is_decoder google mime name')
  Result = namedtuple('Result', 'mn mx p95 med geo p5')
  for comp_, cdata in sorted(data.items()):
    comp = Comp(*comp_)
    section = 'Decoders' if comp.is_decoder else 'Encoders'
    if section != last_section:
      if last_section:
        yield '    </%s>' % last_section
      yield '    <%s>' % section
      last_section = section
    yield '        <MediaCodec name="%s" type="%s" update="true">' % (comp.name, comp.mime)
    for size, sdata in sorted(cdata.items()):
      data = sorted(sdata)
      N = len(data)
      mn, mx = data[0], data[-1]

      if N < 20 and not A.ignore:
        raise ValueError("need at least 20 data points for %s size %s; have %s" %
                         (comp.name, size, N))

      TO = 2.2     # tolerance with margin
      T = TO / 1.1 # tolerance without margin

      Final = namedtuple('Final', 'comment c2 var qual')
      lastFinal = None
      for RG in (10, 15, 20, 25, 30, 40, 50):
        P = 50./RG
        quality = 0
        p95, med, p5 = perc(data, P, math.floor), perc(data, 50, round), perc(data, 100 - P, math.ceil)
        geo = math.sqrt(p5 * p95)
        comment = ''
        pub_lo, pub_hi = min(int(p95 * T), round(geo)), max(math.ceil(p5 / T), round(geo))
        if pub_lo > med:
          if pub_lo > med * 1.1:
            quality += 0.5
            comment += ' SLOW'
          pub_lo = int(med)
        if N < 2 * RG:
          comment += ' N=%d' % N
          quality += 2
        RGVAR = False
        if p5 / p95 > T ** 3:
          quality += 3
          RGVAR = True
          if pub_hi > pub_lo * TO:
            quality += 1
            if RG == 10:
              # find best pub_lo and pub_hi
              for i in range(N // 2):
                pub_lo_, pub_hi_ = min(int(data[N // 2 - i - 1] * T), round(geo), int(med)), max(math.ceil(data[N // 2 + i] / T), round(geo))
                if pub_hi_ > pub_lo_ * TO:
                  # ???
                  pub_lo = min(pub_lo, math.ceil(pub_hi_ / TO))
                  break
                pub_lo, pub_hi = pub_lo_, pub_hi_
        if mn < pub_lo / T or mx > pub_hi * T or pub_lo <= pub_hi / T:
          quality += 1
          comment += ' FLAKY('
          if round(mn, 1) < pub_lo / T:
            comment += 'mn=%.1f < ' % mn
          comment += 'RANGE'
          if round(mx, 1) > pub_hi * T:
            comment += ' < mx=%.1f' % mx
          comment += ')'
        if False:
          comment += ' DATA(mn=%1.f p%d=%1.f accept=%1.f-%1.f p50=%1.f p%d=%1.f mx=%1.f)' % (
            mn, 100-P, p95, pub_lo / T, pub_hi * T, med, P, p5, mx)
        var = math.sqrt(p5/p95)
        if p95 < geo / T or p5 > geo * T:
          if RGVAR:
            comment += ' RG.VARIANCE:%.1f' % ((p5/p95) ** (1./3))
          else:
            comment += ' variance:%.1f' % var
        comment = comment.replace('RANGE', '%d - %d' % (math.ceil(pub_lo / T), int(pub_hi * T)))
        c2 = ''
        if N >= 2 * RG:
          c2 += ' N=%d' % N
        if var <= T or p5 / p95 > T ** 3:
          c2 += ' v%d%%=%.1f' % (round(100 - 2 * P), var)
        if A and A.dbg:
          c2 += ' E=%s' % (str(quality))
        if c2:
          c2 = ' <!--%s -->' % c2

        if comment:
          comment = '            <!-- measured %d%%:%d-%d med:%d%s -->' % (round(100 - 2 * P), int(p95), math.ceil(p5), int(round(med)), comment)
        if A and A.dbg: yield '<!-- --> %s%s' % (comment, c2)
        c2 = '            <Limit name="measured-frame-rate-%s" range="%d-%d" />%s' % (size, pub_lo, pub_hi, c2)
        final = Final(comment, c2, var, quality)
        if lastFinal and final.var > lastFinal.var * math.sqrt(1.3):
          if A and A.dbg: yield '<!-- RANGE JUMP -->'
          break
        elif not lastFinal or quality <= lastFinal.qual:
          lastFinal = final
        if N < 2 * RG or quality >= 4:
          break
      comment, c2, var, quality = lastFinal

      if comment:
        yield comment
      yield c2
    yield '        </MediaCodec>'
  if last_section:
    yield '    </%s>' % last_section
  yield '</MediaCodecs>'
