export const SUPPORTED_LANGUAGES = ["fr", "ar"];

export const CATEGORY_LABELS = {
  All: { fr: "Toutes", ar: "الكل" },
  Economy: { fr: "Economie", ar: "الاقتصاد" },
  Health: { fr: "Sante", ar: "الصحة" },
  Technology: { fr: "Technologie", ar: "التكنولوجيا" },
  Society: { fr: "Societe", ar: "المجتمع" },
  Sports: { fr: "Sports", ar: "الرياضة" },
  Politics: { fr: "Politique", ar: "السياسة" },
  International: { fr: "International", ar: "الدولي" },
};

export const CREDIBILITY_LABELS = {
  Reliable: { fr: "Fiable", ar: "موثوق" },
  "Needs Context": { fr: "Contexte requis", ar: "يحتاج سياقا" },
  Unverified: { fr: "Non verifie", ar: "غير متحقق منه" },
  Suspicious: { fr: "Suspect", ar: "مشبوه" },
  "High Risk": { fr: "Risque eleve", ar: "خطر مرتفع" },
  "No Input": { fr: "Aucune entree", ar: "لا توجد مدخلات" },
};

export const VERIFICATION_STATUSES = {
  "Awaiting stronger corroboration": {
    fr: "En attente d'une corroboration plus solide",
    ar: "بانتظار تأكيد اقوى",
  },
  "Partially corroborated": {
    fr: "Partiellement corrobore",
    ar: "مدعوم جزئيا",
  },
  "Broadly corroborated": {
    fr: "Largement corrobore",
    ar: "مدعوم على نطاق واسع",
  },
  "No verification yet": {
    fr: "Pas encore verifie",
    ar: "لا يوجد تحقق بعد",
  },
  "No content provided": {
    fr: "Aucun contenu fourni",
    ar: "لم يتم توفير محتوى",
  },
  "supported by stronger sources": {
    fr: "soutenu par des sources plus solides",
    ar: "مدعوم بمصادر اقوى",
  },
  "needs context": {
    fr: "necessite plus de contexte",
    ar: "يحتاج الى سياق",
  },
  "suspicious signals": {
    fr: "signaux suspects",
    ar: "اشارات مشبوهة",
  },
  "limited-context analysis": {
    fr: "analyse a contexte limite",
    ar: "تحليل بسياق محدود",
  },
  unverified: {
    fr: "non verifie",
    ar: "غير متحقق منه",
  },
};

export const TRUST_LEVEL_LABELS = {
  high: { fr: "eleve", ar: "مرتفع" },
  medium: { fr: "moyen", ar: "متوسط" },
  low: { fr: "faible", ar: "منخفض" },
  mixed: { fr: "mixte", ar: "مختلط" },
  unknown: { fr: "inconnu", ar: "غير معروف" },
};

export const dictionaries = {
  fr: {
    meta: {
      languageName: "Francais",
      direction: "ltr",
      appDescription:
        "Tableau de bord TruthLens pour surveiller les actualites, les tendances et la credibilite.",
    },
    app: {
      monitoringStudio: "Monitoring studio",
      signedIn: "Connecte",
      assistantReady: "Assistant pret pour Gemini",
      version: "TruthLens v1.0",
    },
    actions: {
      send: "Envoyer",
      clear: "Effacer",
      close: "Fermer",
      login: "Connexion",
      signup: "Creer un compte",
      logout: "Se deconnecter",
      openArticle: "Ouvrir l'article",
      changeTheme: "Changer le theme",
      changeLanguage: "Changer la langue",
      openAssistant: "Ouvrir l'assistant",
      closeAssistant: "Fermer l'assistant",
    },
    theme: {
      light: "Clair",
      dark: "Sombre",
    },
    language: {
      switcher: "Langue",
      fr: "FR",
      ar: "AR",
    },
    nav: {
      dashboard: "Dashboard",
      trending: "Tendances",
      history: "Historique",
      categories: "Categories",
      statistics: "Statistiques",
    },
    regions: {
      morocco: "Maroc",
      world: "Monde",
    },
    topbar: {
      searchPlaceholder: "Rechercher une actualite, une source, un sujet...",
      notifications: "Notifications",
      profile: "Profil",
    },
    assistant: {
      title: "Verification Copilot",
      online: "En ligne",
      placeholder: "Posez votre question...",
      loading: "Je prepare la reponse...",
      welcomeDefault:
        "Bonjour! Je suis votre assistant TruthLens. Comment puis-je vous aider a verifier des informations aujourd'hui?",
      welcomeArticle:
        "Bonjour! Je suis votre assistant TruthLens. Je peux resumer cet article, expliquer son score de credibilite et vous indiquer quoi verifier ensuite.",
      welcomeTrend:
        "Bonjour! Je suis votre assistant TruthLens. Je peux vous expliquer pourquoi cette tendance monte et quels signaux verifier ensuite.",
      unavailable:
        "L'assistant ne peut pas repondre pour le moment.",
      unavailableReply:
        "Je ne peux pas repondre pour le moment. Reessayez dans un instant ou selectionnez un article pour me donner plus de contexte.",
      empty:
        "Posez une question, collez une URL ou une affirmation, et TruthLens Assistant vous aidera a la verifier.",
      readyNotificationTitle: "Assistant pret",
      readyNotificationMessage: "TruthLens Assistant a repondu.",
      failedNotificationTitle: "Assistant indisponible",
      failedNotificationMessage: "La requete assistant a echoue.",
      quickExplain: "Explique ce claim",
      quickVerify: "Que dois-je verifier ensuite ?",
      quickCompare: "Compare les sources",
      quickRisk: "Resume le risque",
    },
    dashboard: {
      kicker: "Analyse de credibilite en temps reel",
      title: "Viral News Monitor",
      subtitle:
        "Suivi en direct du Maroc et du Monde avec badges de credibilite, intelligence de tendance hybride et assistant de verification integre.",
      liveData: "Donnees backend en direct",
      backendConnected: "Backend FastAPI + SQLite + JWT connecte",
      lastRefresh: "Dernier rafraichissement: {batch}",
      resultsCount: "{count} article(s) pour {region}",
      focus: "Focus: {value}",
      allCategories: "toutes les categories",
      loadingTitle: "Chargement des actualites...",
      loadingMessage:
        "Le tableau de bord charge les actualites en direct depuis le backend.",
      errorTitle: "Erreur de chargement",
      noResultsTitle: "Aucun resultat pour ces filtres",
      noResultsMessage:
        "Essayez une autre recherche ou revenez a la vue complete pour continuer l'exploration.",
      newsUpdatedTitle: "Actualites mises a jour",
      newsUpdatedMessage: "{count} article(s) charges pour {region}.",
      whyNowKicker: "Pourquoi c'est important maintenant",
      whyNowLead: "Une rumeur virale peut se propager en quelques minutes. La verification ne devrait pas prendre des heures.",
      whyNowCalm: "Ne paniquez pas. Verifiez d'abord.",
      claimsCheckedToday: "verifications aujourd'hui",
      confidenceCard: "Carte de confiance",
      confidenceLevel: "Niveau de confiance",
      topSignals: "Signaux principaux",
      nextBestAction: "Prochaine meilleure action",
      compareNarrative: "Comparer la narrative",
      sharedNarrative: "Narrative partagee",
      reliableReporting: "Ce que disent les sources fiables",
      stillUnverified: "Ce qui reste non verifie",
      changedOverTime: "Ce qui a evolue",
      claimTimeline: "Chronologie du claim",
      firstAppearance: "Premiere apparition",
      acceleration: "Acceleration",
      verificationMoment: "Moment de verification",
      crisisMode: "Mode crise",
      crisisSubtitle: "Contexte sensible detecte. Les sources les mieux corroborees sont prioritaires.",
      verifiedFirst: "Sources fiables en premier",
      unconfirmed: "Ce qui reste non confirme",
    },
    trending: {
      kicker: "Vue tendances",
      title: "Tendances",
      subtitle:
        "Vue rapide des sujets les plus actifs pour {region}.",
      liveSnapshot: "Instantane des tendances",
      loadingTitle: "Chargement des tendances...",
      loadingMessage: "Les tendances se chargent depuis le backend.",
      emptyTitle: "Aucune tendance",
      emptyMessage:
        "Aucune tendance n'est disponible pour cette region pour le moment.",
      intelligence: "Intelligence de tendance",
      earlyWarning: "Alerte precoce",
      virality: "Viralite",
      articles: "Articles",
      gap: "Ecart",
      whyItTrends: "Pourquoi cela monte",
      riskLevel: "Niveau de risque",
      sampleHeadlines: "Exemples de titres",
      checkCount: "Verifications",
      trendReason:
        "En tendance car ce sujet apparait dans plusieurs articles recents et demandes de verification.",
    },
    history: {
      kicker: "Intelligence archivee",
      title: "Actualites historiques",
      subtitle:
        "Actualites stockees dans SQLite avec leur analyse de credibilite enregistree.",
      storedFeed: "Flux d'analyse stocke",
      archivedCount: "{count} article(s) archives pour {region}",
      searchScope: 'Portee de recherche: {value}',
      allStoredCoverage: "toute la couverture stockee",
      loadingTitle: "Chargement des actualites historiques...",
      loadingMessage: "L'archive stockee se charge depuis le backend.",
      errorTitle: "Erreur de chargement de l'archive",
      emptyTitle: "Aucune actualite historique",
      emptyMessage:
        "Essayez une autre recherche ou changez de region/categorie pour explorer l'archive.",
      storedAnalysis: "Analyse stockee",
      savedCredibility: "Analyse de credibilite enregistree",
      published: "Publie",
      stored: "Stocke",
      analyzed: "Analyse",
      verificationUnavailable: "Statut de verification indisponible",
    },
    categories: {
      kicker: "Vue categories",
      title: "Categories",
      subtitle: "Repartition de la couverture backend par categorie.",
      snapshot: "Instantane categories backend",
      category: "Categorie",
      description:
        "Nombre d'articles actuellement disponibles dans cette categorie.",
      noDataTitle: "Aucune donnee categorie",
      noDataMessage:
        "Aucune donnee categorie n'est disponible pour la region selectionnee.",
      value: "Valeur",
      watch: "A surveiller",
    },
    statistics: {
      kicker: "Metriques systeme",
      title: "Statistiques",
      subtitle:
        "Activite du systeme, volume de verification et metriques de monitoring.",
      sqliteMetrics: "Metriques SQLite",
      todayActivity: "Activite du jour",
      articlesLoaded: "articles actuellement charges",
      storiesFlagged: "contenus signales pour revue",
      moroccoArticles: "articles Maroc",
      worldArticles: "articles Monde",
    },
    article: {
      credibility: "Credibilite",
      trend: "Tendance",
      trust: "Confiance",
      source: "Source",
      articleQuality: "Article",
      corroboration: "Corroboration",
      justNow: "A l'instant",
      minutesAgo: "min",
      hoursAgo: "h",
    },
    analysis: {
      ready: "Pret pour l'analyse",
      noInputYet: "Aucune entree",
      noContentProvided: "Aucun contenu fourni",
      waitingInput: "En attente d'une saisie utilisateur",
      noRiskSignal: "Aucun signal de risque majeur detecte",
      sourceBaselineStrong: "Bonne base de confiance source detectee",
      moreContextRequired: "Plus de contexte est necessaire",
      earlySignal: "Signal precoce detecte",
      suspicious: "Contenu suspect",
      highRisk: "Contenu a risque eleve",
      analysisComplete: "Analyse terminee",
    },
    statuses: {
      fresh: "frais",
      active: "actif",
      watch: "surveillance",
      noInputYet: "Aucune entree",
      notAvailable: "Non disponible",
    },
    auth: {
      connectedUser: "Utilisateur connecte",
      email: "Email",
      name: "Nom",
      notProvided: "Non renseigne",
      fullNamePlaceholder: "Nom complet",
      emailPlaceholder: "Email",
      passwordPlaceholder: "Mot de passe",
      pleaseWait: "Veuillez patienter...",
      loginSuccessTitle: "Connexion reussie",
      loginSuccessMessage: "Connecte en tant que {user}",
      registerSuccessTitle: "Compte cree",
      registerSuccessMessage: "Bienvenue {user}",
      logoutTitle: "Deconnexion",
      logoutMessage: "Votre session a ete fermee.",
    },
    notifications: {
      title: "Notifications",
      empty: "Aucune notification pour le moment.",
    },
  },
  ar: {
    meta: {
      languageName: "العربية",
      direction: "rtl",
      appDescription:
        "لوحة TruthLens لمراقبة الاخبار والاتجاهات وتحليل المصداقية.",
    },
    app: {
      monitoringStudio: "استوديو المراقبة",
      signedIn: "متصل",
      assistantReady: "مساعد جاهز مع Gemini",
      version: "TruthLens v1.0",
    },
    actions: {
      send: "إرسال",
      clear: "مسح",
      close: "إغلاق",
      login: "تسجيل الدخول",
      signup: "إنشاء حساب",
      logout: "تسجيل الخروج",
      openArticle: "فتح المقال",
      changeTheme: "تغيير النمط",
      changeLanguage: "تغيير اللغة",
      openAssistant: "فتح المساعد",
      closeAssistant: "إغلاق المساعد",
    },
    theme: {
      light: "فاتح",
      dark: "داكن",
    },
    language: {
      switcher: "اللغة",
      fr: "FR",
      ar: "AR",
    },
    nav: {
      dashboard: "لوحة المتابعة",
      trending: "الاتجاهات",
      history: "الارشيف",
      categories: "الفئات",
      statistics: "الاحصاءات",
    },
    regions: {
      morocco: "المغرب",
      world: "العالم",
    },
    topbar: {
      searchPlaceholder: "ابحث عن خبر او مصدر او موضوع...",
      notifications: "الإشعارات",
      profile: "الملف الشخصي",
    },
    assistant: {
      title: "مساعد التحقق",
      online: "متصل",
      placeholder: "اكتب سؤالك...",
      loading: "يتم تجهيز الرد...",
      welcomeDefault:
        "مرحبا! انا مساعد TruthLens. كيف يمكنني مساعدتك اليوم في التحقق من المعلومات؟",
      welcomeArticle:
        "مرحبا! يمكنني تلخيص هذا المقال وشرح درجة المصداقية واقتراح ما يجب التحقق منه بعد ذلك.",
      welcomeTrend:
        "مرحبا! يمكنني شرح سبب تصاعد هذا الاتجاه وما هي الاشارات التي يجب التحقق منها.",
      unavailable: "المساعد غير قادر على الرد حاليا.",
      unavailableReply:
        "لا يمكنني الرد حاليا. حاول مرة اخرى بعد قليل او اختر مقالا لاعطائي سياقا اوضح.",
      empty:
        "اطرح سؤالا او الصق رابطا او ادعاء، وسيساعدك TruthLens Assistant على التحقق منه.",
      readyNotificationTitle: "المساعد جاهز",
      readyNotificationMessage: "قام TruthLens Assistant بالرد.",
      failedNotificationTitle: "المساعد غير متاح",
      failedNotificationMessage: "فشل طلب المساعد.",
      quickExplain: "اشرح هذا الادعاء",
      quickVerify: "ما الذي يجب التحقق منه بعد ذلك؟",
      quickCompare: "قارن المصادر",
      quickRisk: "لخص مستوى الخطر",
    },
    dashboard: {
      kicker: "تحليل المصداقية في الوقت الفعلي",
      title: "مراقب الاخبار الرائجة",
      subtitle:
        "متابعة مباشرة للمغرب والعالم مع شارات المصداقية وذكاء الاتجاهات ومساعد تحقق مدمج.",
      liveData: "بيانات مباشرة من الخلفية",
      backendConnected: "FastAPI + SQLite + JWT متصل",
      lastRefresh: "اخر تحديث: {batch}",
      resultsCount: "{count} مقال لـ {region}",
      focus: "التركيز: {value}",
      allCategories: "كل الفئات",
      loadingTitle: "جاري تحميل الاخبار...",
      loadingMessage: "تقوم اللوحة بتحميل الاخبار المباشرة من الخلفية.",
      errorTitle: "خطأ في التحميل",
      noResultsTitle: "لا توجد نتائج لهذه الفلاتر",
      noResultsMessage:
        "جرب بحثا اخر او عد الى عرض الكل لمواصلة الاستكشاف.",
      newsUpdatedTitle: "تم تحديث الاخبار",
      newsUpdatedMessage: "تم تحميل {count} مقال لـ {region}.",
      whyNowKicker: "لماذا هذا مهم الآن",
      whyNowLead: "يمكن لادعاء فيروسي أن ينتشر خلال دقائق، لكن التحقق يجب ألا يستغرق ساعات.",
      whyNowCalm: "لا داعي للذعر. تحقق أولا.",
      claimsCheckedToday: "عمليات تحقق اليوم",
      confidenceCard: "بطاقة الثقة",
      confidenceLevel: "مستوى الثقة",
      topSignals: "أهم الإشارات",
      nextBestAction: "أفضل خطوة تالية",
      compareNarrative: "قارن السردية",
      sharedNarrative: "السردية المتداولة",
      reliableReporting: "ماذا تقول التغطية الأكثر موثوقية",
      stillUnverified: "ما الذي لا يزال غير متحقق منه",
      changedOverTime: "ما الذي تغير مع الوقت",
      claimTimeline: "خط زمني للادعاء",
      firstAppearance: "أول ظهور",
      acceleration: "التسارع",
      verificationMoment: "لحظة التحقق",
      crisisMode: "وضع الأزمة",
      crisisSubtitle: "تم رصد سياق حساس. يتم إعطاء الأولوية للمصادر الأكثر دعما.",
      verifiedFirst: "المصادر الموثقة أولا",
      unconfirmed: "ما الذي لا يزال غير مؤكد",
    },
    trending: {
      kicker: "نظرة على الاتجاهات",
      title: "الاتجاهات",
      subtitle: "عرض سريع لاكثر المواضيع نشاطا في {region}.",
      liveSnapshot: "لقطة مباشرة للاتجاهات",
      loadingTitle: "جاري تحميل الاتجاهات...",
      loadingMessage: "يتم تحميل الاتجاهات من الخلفية.",
      emptyTitle: "لا توجد اتجاهات",
      emptyMessage: "لا توجد اتجاهات متاحة لهذه المنطقة حاليا.",
      intelligence: "ذكاء الاتجاهات",
      earlyWarning: "إنذار مبكر",
      virality: "الانتشار",
      articles: "المقالات",
      gap: "الفجوة",
      whyItTrends: "سبب التصاعد",
      riskLevel: "مستوى الخطر",
      sampleHeadlines: "عناوين نموذجية",
      checkCount: "عمليات التحقق",
      trendReason:
        "هذا الموضوع رائج لأنه يظهر عبر عدة مقالات حديثة وعمليات تحقق للمستخدمين.",
    },
    history: {
      kicker: "ذكاء الارشيف",
      title: "الاخبار التاريخية",
      subtitle:
        "اخبار محفوظة في SQLite مع تحليل المصداقية المخزن لكل مقال.",
      storedFeed: "تحليلات محفوظة",
      archivedCount: "{count} مقال مؤرشف لـ {region}",
      searchScope: "نطاق البحث: {value}",
      allStoredCoverage: "كل التغطية المخزنة",
      loadingTitle: "جاري تحميل الاخبار التاريخية...",
      loadingMessage: "يتم تحميل الارشيف المخزن من الخلفية.",
      errorTitle: "خطأ في تحميل الارشيف",
      emptyTitle: "لا توجد اخبار تاريخية",
      emptyMessage:
        "جرب بحثا اخر او غيّر المنطقة/الفئة لاستكشاف الارشيف.",
      storedAnalysis: "تحليل محفوظ",
      savedCredibility: "تحليل المصداقية المحفوظ",
      published: "نشر",
      stored: "حفظ",
      analyzed: "تحليل",
      verificationUnavailable: "حالة التحقق غير متاحة",
    },
    categories: {
      kicker: "نظرة على الفئات",
      title: "الفئات",
      subtitle: "توزيع التغطية الخلفية حسب الفئة.",
      snapshot: "لقطة فئات من الخلفية",
      category: "الفئة",
      description: "عدد المقالات المتاحة حاليا في هذه الفئة.",
      noDataTitle: "لا توجد بيانات فئات",
      noDataMessage: "لا توجد بيانات فئات متاحة لهذه المنطقة.",
      value: "القيمة",
      watch: "للمراقبة",
    },
    statistics: {
      kicker: "مقاييس النظام",
      title: "الاحصاءات",
      subtitle: "نشاط النظام وحجم التحقق ومقاييس المتابعة.",
      sqliteMetrics: "مقاييس SQLite",
      todayActivity: "نشاط اليوم",
      articlesLoaded: "مقالات محملة حاليا",
      storiesFlagged: "قصص بحاجة لمراجعة",
      moroccoArticles: "مقالات المغرب",
      worldArticles: "مقالات العالم",
    },
    article: {
      credibility: "المصداقية",
      trend: "الاتجاه",
      trust: "الثقة",
      source: "المصدر",
      articleQuality: "المقال",
      corroboration: "التعزيز",
      justNow: "الان",
      minutesAgo: "د",
      hoursAgo: "س",
    },
    analysis: {
      ready: "جاهز للتحليل",
      noInputYet: "لا توجد مدخلات",
      noContentProvided: "لم يتم توفير محتوى",
      waitingInput: "بانتظار ادخال المستخدم",
      noRiskSignal: "لا توجد اشارة خطر كبيرة",
      sourceBaselineStrong: "تم رصد اساس قوي للمصدر",
      moreContextRequired: "هناك حاجة الى مزيد من السياق",
      earlySignal: "تم رصد اشارة مبكرة",
      suspicious: "محتوى مشبوه",
      highRisk: "محتوى عالي الخطورة",
      analysisComplete: "اكتمل التحليل",
    },
    statuses: {
      fresh: "حديث",
      active: "نشط",
      watch: "مراقبة",
      noInputYet: "لا توجد مدخلات",
      notAvailable: "غير متاح",
    },
    auth: {
      connectedUser: "المستخدم المتصل",
      email: "البريد الالكتروني",
      name: "الاسم",
      notProvided: "غير متوفر",
      fullNamePlaceholder: "الاسم الكامل",
      emailPlaceholder: "البريد الالكتروني",
      passwordPlaceholder: "كلمة المرور",
      pleaseWait: "يرجى الانتظار...",
      loginSuccessTitle: "تم تسجيل الدخول",
      loginSuccessMessage: "تم الاتصال باسم {user}",
      registerSuccessTitle: "تم انشاء الحساب",
      registerSuccessMessage: "مرحبا {user}",
      logoutTitle: "تسجيل الخروج",
      logoutMessage: "تم اغلاق الجلسة.",
    },
    notifications: {
      title: "الاشعارات",
      empty: "لا توجد اشعارات حاليا.",
    },
  },
};

function getNestedValue(object, key) {
  return key.split(".").reduce((current, part) => current?.[part], object);
}

export function getTranslator(language = "fr") {
  const dictionary = dictionaries[language] || dictionaries.fr;

  return function t(key, params = {}) {
    const template = getNestedValue(dictionary, key) ?? getNestedValue(dictionaries.fr, key) ?? key;

    if (typeof template !== "string") {
      return key;
    }

    return template.replace(/\{(\w+)\}/g, (_, token) => `${params[token] ?? ""}`);
  };
}

export function getDirection(language = "fr") {
  return dictionaries[language]?.meta?.direction || "ltr";
}

export function translateCategory(value, language = "fr") {
  return CATEGORY_LABELS[value]?.[language] || value;
}

export function translateCredibilityLabel(value, language = "fr") {
  return CREDIBILITY_LABELS[value]?.[language] || value;
}

export function translateVerificationStatus(value, language = "fr") {
  return VERIFICATION_STATUSES[value]?.[language] || value;
}

export function translateTrustLevel(value, language = "fr") {
  return TRUST_LEVEL_LABELS[value]?.[language] || value;
}
