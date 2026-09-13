# Autonomic M401 – Home Assistant

Custom integration for an Autonomic M401/M400-style amplifier.

## Configured zones

- Küche: zone 5
- Wohnzimmer: zone 6
- Bad: zone 7
- Schlafzimmer: zone 8

## Features

Each zone gets:
- Power (switch)
- Volume 0–100 % (number)
- Mute (switch)
- Source S1–S8 (select)

The integration polls the amplifier every 3 seconds and also updates the Home Assistant state immediately after a command.

## Protocol

The Autonomic amplifier control protocol uses TCP port 17037 and ASCII-hex commands terminated by LF.

Examples:
- Zone 5 ON: `010501`
- Zone 5 OFF: `010500`
- Zone 5 mute: `020500`
- Zone 5 unmute: `020501`
- Zone 5 source S1: `030505`
- Zone 5 volume: command `04`, zone `05`, followed by the volume value in the documented A0 range.

## Installation

1. Copy `custom_components/autonomic_m401` into `/config/custom_components/`.
2. Copy `www/autonomic-m401-card.js` into `/config/www/`.
3. Restart Home Assistant.
4. Go to Settings → Devices & services → Add integration → Autonomic M401.
5. Enter the amplifier IP address. Keep TCP port 17037.
6. Enter zones `5,6,7,8` and names `Küche,Wohnzimmer,Bad,Schlafzimmer`.

## Lovelace card

Add the JS file as a dashboard resource:

URL:
`/local/autonomic-m401-card.js`

Resource type:
`JavaScript module`

Then add a manual card:

```yaml
type: custom:autonomic-m401-card
title: Multiroom Audio
entities:
  - name: Küche
    power: switch.autonomic_m401_zone_5_power
    volume: number.autonomic_m401_zone_5_volume
    mute: switch.autonomic_m401_zone_5_mute
    source: select.autonomic_m401_zone_5_source
  - name: Wohnzimmer
    power: switch.autonomic_m401_zone_6_power
    volume: number.autonomic_m401_zone_6_volume
    mute: switch.autonomic_m401_zone_6_mute
    source: select.autonomic_m401_zone_6_source
  - name: Bad
    power: switch.autonomic_m401_zone_7_power
    volume: number.autonomic_m401_zone_7_volume
    mute: switch.autonomic_m401_zone_7_mute
    source: select.autonomic_m401_zone_7_source
  - name: Schlafzimmer
    power: switch.autonomic_m401_zone_8_power
    volume: number.autonomic_m401_zone_8_volume
    mute: switch.autonomic_m401_zone_8_mute
    source: select.autonomic_m401_zone_8_source
```

## Important

The source protocol documents S1–S8 and maps them to protocol values. If you use custom source names in the amplifier, the card currently still displays S1–S8; this can be extended with configurable source labels.

The volume command is implemented using the documented A0 range. Because the documentation does not fully specify a user-facing dB/percent conversion, Home Assistant presents it as 0–100 %. Test the first volume change at a low value.
