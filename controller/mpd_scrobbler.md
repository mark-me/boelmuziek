# Possible MPD states

## Scrobbler starts when MPD is

### Playing a track

* **Action**: Set now playing

```python
{
    'player_state': 'play',
    'file': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3',
    'duration': 704.182,
    'elapsed': 175.438,
    'file_previous': None,
    'stopwatch_paused': False,
    'stopwatch_seconds': 0.003942966461181641
}
```

### Paused

* **Action**: Do nothing

```python
{
    'player_state': 'pause',
    'file': 'Gerry Mulligan & Paul Desmond/Blues in Time/01 Blues in Time.flac',
    'duration': 540.473,
    'elapsed': 7.695,
    'file_previous': None,
    'duration_previous': None,
    'stopwatch_paused': True,
    'stopwatch_seconds': 2.4318695068359375e-05
}
```

### Stopped

* **Action**: Do nothing

```python
{
    'player_state': 'stop',
    'file': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3',
    'duration': 704.182,
    'elapsed': None,
    'file_previous': None,
    'stopwatch_paused': False,
    'stopwatch_seconds': 0
}
```

### Empty playlist

* **Action**: Do nothing

```python
{
    'player_state': 'stop',
    'file': None,
    'duration': None,
    'elapsed': None,
    'file_previous': None,
    'stopwatch_paused': False,
    'stopwatch_seconds': 0
}
```

## Scrobbler after startup

### Play

### After stop

```python
{
    'player_state': 'play',
    'file': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3',
    'duration': 704.182,
    'elapsed': 0.0,
    'file_previous': None,
    'stopwatch_paused': False,
    'stopwatch_seconds': 0
}
```

```python
{
    'player_state': 'play',
    'file': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3',
    'duration': 704.182,
    'elapsed': 0.0,
    'file_previous': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3',
    'stopwatch_paused': False,
    'stopwatch_seconds': 0.10338926315307617
}
```

#### After pause

```python
{
    'player_state': 'play',
    'file': 'Gerry Mulligan & Paul Desmond/Blues in Time/01 Blues in Time.flac',
    'duration': 540.473,
    'elapsed': 7.717,
    'file_previous': None,
    'duration_previous': None,
    'stopwatch_paused': True,
    'stopwatch_seconds': 2.4318695068359375e-05
}
```

### Seek

* **Action**: Do nothing

```python
{
    'player_state': 'play',
    'file': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3',
    'duration': 704.182,
    'elapsed': 676.0,
    'file_previous': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3',
    'stopwatch_paused': False,
    'stopwatch_seconds': 34.46977925300598
}
```

### Paused

* **Action**: Do nothing

```python
{
    'player_state': 'pause',
    'file': 'A Silver Mt. Zion/Horses in the Sky [2005]/01 God Bless Our Dead Marines.mp3',
    'duration': 704.182,
    'elapsed': 231.386,
    'file_previous': None,
    'stopwatch_paused': False,
    'stopwatch_seconds': 55.964664697647095
}
```

### Stopped

* **Action**: If stopwatch seconds/duration > .5 scrobble, else do nothing

```python
{
    'player_state': 'stop',
    'file': 'Gerry Mulligan & Paul Desmond/Blues in Time/06 Battle Hymn of the Republican.flac',
    'duration': 463.02,
    'elapsed': None,
    'file_previous': 'Gerry Mulligan & Paul Desmond/Blues in Time/06 Battle Hymn of the Republican.flac',
    'duration_previous': 463.02,
    'stopwatch_paused': False,
    'stopwatch_seconds': 41.866673707962036
}
```

### Clear playlist

* **Action**: If stopwatch seconds/duration > .5 scrobble, else do nothing

```python
{
    'player_state': 'stop',
    'file': None,
    'duration': None,
    'elapsed': None,
    'file_previous': 'A Silver Mt. Zion/Horses in the Sky [2005]/02 Mountains Made of Steam.mp3',
    'stopwatch_paused': False,
    'stopwatch_seconds': 124.64062666893005
}
```

### Next track

* **Action**: Scrobble previously played track if stopwatch_seconds/duration_previous >.5, set 'now playing' current track

```python
{
    'player_state': 'play',
    'file': 'Gerry Mulligan & Paul Desmond/Blues in Time/02 Body and Soul.flac',
    'duration': 577.619,
    'elapsed': 0.0,
    'file_previous': 'Gerry Mulligan & Paul Desmond/Blues in Time/01 Blues in Time.flac',
    'duration_previous': 540.473,
    'stopwatch_paused': False,
    'stopwatch_seconds': 532.7409846782684
}
```
