import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import PageIntro from './components/PageIntro.vue'
import LabHome from './components/LabHome.vue'
import ExperimentCatalog from './components/ExperimentCatalog.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout: () => h(DefaultTheme.Layout, null, { 'doc-before': () => h(PageIntro) }),
  enhanceApp({ app }) {
    app.component('LabHome', LabHome)
    app.component('ExperimentCatalog', ExperimentCatalog)
  },
}
