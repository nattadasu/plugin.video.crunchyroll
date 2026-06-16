"""Subtitle gap filling utilities for readability enhancement.

Provides frame-rate aware gap detection and filling for ASS/SSA subtitle format
to improve readability by eliminating distracting rapid transitions between
consecutive subtitle lines.
"""

import re
from typing import List, Tuple, Dict


# Frame rate constants (in frames per second)
F_RATE = 23.976


class TimeStampConverter:
    """Converts between timestamps and seconds for subtitle processing."""

    @staticmethod
    def timestamp_to_seconds(timestamp: str) -> float:
        """Convert ASS timestamp (h:mm:ss.cc) to seconds.

        Args:
            timestamp: ASS format timestamp (e.g., "0:01:30.50")

        Returns:
            Time in seconds as float.
        """
        try:
            parts = timestamp.split(':')
            if len(parts) != 3:
                return 0.0
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            centiseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

            total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
            return total_seconds
        except (ValueError, IndexError):
            return 0.0

    @staticmethod
    def seconds_to_timestamp(seconds: float) -> str:
        """Convert seconds to ASS timestamp (h:mm:ss.cc).

        Args:
            seconds: Time in seconds.

        Returns:
            ASS format timestamp string.
        """
        hours = int(seconds // 3600)
        remaining = seconds % 3600
        minutes = int(remaining // 60)
        secs = remaining % 60

        sec_int = int(secs)
        centisec = int((secs - sec_int) * 100)

        return f"{hours}:{minutes:02d}:{sec_int:02d}.{centisec:02d}"


class ASSGapFiller:
    """Fills distracting subtitle flicker gaps in ASS/SSA format.

    Targets gaps up to 4-6 frames at 24fps (~167-250ms) and extends subtitle
    end times to eliminate rapid transitions that reduce readability while
    preserving intentional 0ms gaps that are often used for sentence splitting.
    """

    def __init__(self, max_gap_frames: float = 4.5, fps: float = F_RATE) -> None:
        """Initialize the ASSGapFiller.

        Args:
            max_gap_frames: Maximum gap in frames to fill. Defaults to 4.5 frames (~187ms at 24fps).
            fps: Frame rate in frames per second. Defaults to 24fps.
        """
        self.max_gap_seconds = max_gap_frames / fps
        self.converter = TimeStampConverter()
        # Pattern to match ASS dialogue lines: Dialogue: layer, start, end, style, name, margin_l, margin_r, margin_v, effect, text
        self.dialogue_pattern = re.compile(
            r'^Dialogue:\s*(\d+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]*),\s*(\d+),\s*(\d+),\s*(\d+),\s*([^,]*),\s*(.*)$',
            re.MULTILINE
        )

    def fill_flicker_gaps(self, subtitle_content: str) -> Tuple[str, int]:
        """Fill distracting gaps between subtitle lines in ASS format.

        Groups dialogue lines by layer and style to ensure we only fill gaps between
        consecutive dialogue lines of the same stream (avoiding background signs/titles).

        Args:
            subtitle_content: The full ASS subtitle file content as string.

        Returns:
            Tuple of (modified_content, gaps_filled_count).
        """
        lines = subtitle_content.split('\n')
        dialogue_groups: Dict[Tuple[str, str], List[Tuple[int, dict]]] = {}

        # Parse all dialogue lines and group them by (layer, style)
        for i, line in enumerate(lines):
            match = self.dialogue_pattern.match(line)
            if match:
                layer = match.group(1)
                start_ts = match.group(2).strip()
                end_ts = match.group(3).strip()
                style = match.group(4)
                
                data = {
                    'layer': layer,
                    'start': start_ts,
                    'end': end_ts,
                    'style': style,
                    'name': match.group(5),
                    'margin_l': match.group(6),
                    'margin_r': match.group(7),
                    'margin_v': match.group(8),
                    'effect': match.group(9),
                    'text': match.group(10),
                }
                
                key = (layer, style)
                if key not in dialogue_groups:
                    dialogue_groups[key] = []
                dialogue_groups[key].append((i, data))

        gaps_filled = 0
        modified_lines = dict(enumerate(lines))  # Keep all lines, will modify dialogue ones

        # For each group, sort by start time and fill gaps
        for key, group in dialogue_groups.items():
            if len(group) <= 1:
                continue
            
            # Sort group by start time in seconds
            group.sort(key=lambda x: self.converter.timestamp_to_seconds(x[1]['start']))
            
            for idx in range(len(group) - 1):
                current_line_idx, current_data = group[idx]
                next_line_idx, next_data = group[idx + 1]

                # Convert timestamps to seconds
                current_end_sec = self.converter.timestamp_to_seconds(current_data['end'])
                next_start_sec = self.converter.timestamp_to_seconds(next_data['start'])

                gap_seconds = next_start_sec - current_end_sec

                # Fill gap if it's between 0 and max_gap_seconds (preserve 0ms gaps)
                if 0 < gap_seconds <= self.max_gap_seconds:
                    # Update the end time to match the next subtitle's start time
                    new_end_ts = next_data['start']
                    current_data['end'] = new_end_ts

                    # Reconstruct the dialogue line with new end timestamp
                    new_line = (
                        f"Dialogue: {current_data['layer']},"
                        f"{current_data['start']},"
                        f"{new_end_ts},"
                        f"{current_data['style']},"
                        f"{current_data['name']},"
                        f"{current_data['margin_l']},"
                        f"{current_data['margin_r']},"
                        f"{current_data['margin_v']},"
                        f"{current_data['effect']},"
                        f"{current_data['text']}"
                    )

                    modified_lines[current_line_idx] = new_line
                    gaps_filled += 1

        # Reconstruct the file
        result_lines = [modified_lines.get(i, line) for i, line in enumerate(lines)]
        return '\n'.join(result_lines), gaps_filled
