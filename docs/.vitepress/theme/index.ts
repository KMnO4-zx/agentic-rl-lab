import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import PageIntro from './components/PageIntro.vue'
import RelatedReading from './components/RelatedReading.vue'
import LocaleSwitch from './components/LocaleSwitch.vue'
import LabHome from './components/LabHome.vue'
import ExperimentCatalog from './components/ExperimentCatalog.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout: () => h(DefaultTheme.Layout, null, { 'doc-before': () => h(PageIntro), 'doc-after': () => h(RelatedReading), 'nav-bar-content-after': () => h(LocaleSwitch) }),
  enhanceApp({ app }) {
    app.component('LabHome', LabHome)
    app.component('ExperimentCatalog', ExperimentCatalog)
  },
}
