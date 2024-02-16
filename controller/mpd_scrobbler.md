# Possible MPD states

## Scrobbler starts when MPD is

### Playing a track

Set now playing

```python
{
    'player_state': 'play',
    'file': "A Silver Mt. Zion/Horses in the Sky [2005]/04 Teddy Roosevelt's Guns.mp3",
    'duration': 585.351,
    'elapsed': 91.134,
    'file_previous': None
}
```

### Paused

Do nothing

```python
{
    'player_state': 'pause',
    'file': "A Silver Mt. Zion/Horses in the Sky [2005]/04 Teddy Roosevelt's Guns.mp3",
    'duration': 585.351,
    'elapsed': 81.811,
    'file_previous': None
}
```

### Stopped

Do nothing

```python
{
    'player_state': 'stop',
    'file': 'Joe Henderson/Mode for Joe/03 Black.flac',
    'duration': 411.866,
    'elapsed': None,
    'file_previous': None
}
```

### Empty playlist

Do nothing

```python
{
    'player_state': 'stop',
    'file': None,
    'duration': None,
    'elapsed': None,
    'file_previous': None
}
```

## Scrobbler after startup

### Play

```python
{
    'player_state': 'play',
    'file': 'Joe Henderson/Mode for Joe/03 Black.flac',
    'duration': 411.866,
    'elapsed': 0.0,
    'file_previous': 'Joe Henderson/Mode for Joe/03 Black.flac'
}
```

### Paused

```python
{
    'player_state': 'pause',
    'file': 'Joe Henderson/Mode for Joe/03 Black.flac',
    'duration': 411.866,
    'elapsed': 85.829,
    'file_previous': 'Joe Henderson/Mode for Joe/03 Black.flac'
}
```

### Stopped

```python
{
    'player_state': 'stop',
    'file': 'Joe Henderson/Mode for Joe/07 Black (alternate take).flac',
    'duration': 408.453,
    'elapsed': None,
    'file_previous': 'Joe Henderson/Mode for Joe/07 Black (alternate take).flac'
}
```

### Clear playlist

```python
{
    'player_state': 'stop',
    'file': None,
    'duration': None,
    'elapsed': None,
    'file_previous': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3'
}
```

### Next/previous track

```python
{
    'player_state': 'play',
    'file': 'Joe Henderson/Mode for Joe/07 Black (alternate take).flac',
    'duration': 408.453,
    'elapsed': 0.0,
    'file_previous': 'Joe Henderson/Mode for Joe/03 Black.flac'
}
```
