import {
    loadDataAccess
} from "../modules/data-access/data-access.js";

import {
    loadSystems
} from "../modules/systems/systems.js";

import {
    loadAssets
} from "../modules/assets/assets.js";

import {
    loadSensitive
} from "../modules/sensitive/sensitive.js";

import {
    loadPolicies
} from "../modules/policies/policies.js";

import {
    loadAudit
} from "../modules/audit/audit.js";

import {
    loadDataSources
} from "../modules/data-sources/data-sources.js";



export const viewRegistry = {

    customers: {
        title: "业务数据访问",

        description:
            "访问受控业务数据并执行动态安全策略",

        load: loadDataAccess
    },


    systems: {
        title: "业务系统管理",

        description:
            "管理接入平台的业务系统及基础信息",

        load: loadSystems
    },


    dataSources: {
        title: "数据源管理",

        description:
            "管理业务系统下的数据源连接及运行状态",

        load: loadDataSources
    },


    assets: {
        title: "资产管理",

        description:
            "管理业务系统、数据源及数据库资产目录",

        load: loadAssets
    },


    sensitive: {
        title: "敏感数据管理",

        description:
            "查看敏感字段识别、分类分级及人工复核结果",

        load: loadSensitive
    },


    policies: {
        title: "安全策略",

        description:
            "查看当前访问控制与脱敏策略",

        load: loadPolicies
    },


    audit: {
        title: "行为审计",

        description:
            "查看系统访问和策略执行记录",

        load: loadAudit
    }
};