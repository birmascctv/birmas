import forms from '@tailwindcss/forms'
import typography from '@tailwindcss/typography'

export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts}'
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [
    forms,
    typography,
  ],
}
