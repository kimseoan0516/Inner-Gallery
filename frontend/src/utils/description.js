export function generateDescription(art) {
  const title = art.titleKo || art.title;
  const artist = art.artistKo || art.artist;
  const year = art.year ? ` (${art.year})` : '';
  // Simple placeholder description; can be expanded with more details.
  return `${title}${year} by ${artist} is a remarkable artwork that showcases the artist's skill and vision. It is celebrated for its composition, use of color, and historical significance.`;
}
