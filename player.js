const ytdl = require('ytdl-core');
const ffmpeg = require('fluent-ffmpeg');
const through = require('through2');

const Speaker = require('speaker');
const { Decoder } = require('lame');

const AUDIO_COMPLETED = 0;
const AUDIO_TERMINATED = 1;

let video = null;
let audioStream = null;
let speaker = null;
module.exports.video = video;

function isPlaying() {
  return video && speaker && audioStream;
}
module.exports.isPlaying = isPlaying;

function isLoading() {
  return video && audioStream && !speaker;
}
module.exports.isLoading = isLoading;

function play(vid) {
  return new Promise((resolve, reject) => {
    if (video == null) {
      video = ytdl(vid, {
        format: 'mp3',
      });

      video.on('info', (info) => {
        const {
          title, loudness, relative_loudness, length_seconds, thumbnail_url,
        } = info;
        video.info = {
          title, loudness, relative_loudness, length_seconds, thumbnail_url,
        };
      });

      const stream = through();
      audioStream = ffmpeg(video).format('mp3').pipe(stream).pipe(Decoder());

      audioStream.on('format', (format) => {
        // Create a new speaker with the given format.
        speaker = new Speaker(format);

        // Handle the speaker finishing its audio stream.
        speaker.on('close', () => {
          video = null;
          speaker = null;
          audioStream = null;
          resolve(AUDIO_COMPLETED);
        });

        // Pipe the decoded audio into the speaker.
        audioStream = audioStream.pipe(speaker);
      });

      // Audio Stream Termination
      audioStream.on('finish', () => {
        if (isLoading()) {
          speaker = null;
          resolve(AUDIO_TERMINATED);
        }
      });

      // An error occurred.
      audioStream.on('error', (error) => {
        console.log('Failed to play YouTube video.', error.toString());
        reject(error);
      });

      // The stream was closed externally.
      audioStream.on('close', (error) => {
        console.log('Closing audio stream on request.', error.toString());
        reject(error);
      });
    } else {
      const err = new Error('Already playing a song.');
      reject(err);
    }
  });
}
module.exports.play = play;

function stop() {
  if (isPlaying()) {
    console.log('Stop requested while playing. Stopping audio.');
    speaker.end();
    audioStream.end();
    video = null;
  } else if (isLoading()) {
    console.log('Stop requested while loading. Cleaning up.');
    audioStream.end();
    video = null;
  } else {
    console.log('Nothing is currently video.');
  }
}
module.exports.stop = stop;

function getInfo() {
  if (video == null) {
    return null;
  }
  return video.info;
}
module.exports.getInfo = getInfo;
